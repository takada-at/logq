#include <Python.h>
#include <structmember.h>

#include "engine.h"
#include "ltsv.h"
#include "colmap.h"

/**
 * LTSVParser
 */

static PyObject *ltsv_error_obj;     /* LTSV exception */
static long field_limit = 128 * 1024;   /* max parsed field size */

staticforward PyTypeObject LTSVParser_Type;

#define LTSVParser_Check(v)   (Py_TYPE(v) == &LTSVParser_Type)

static int
parse_save_label(LTSVParser *self)
{
    self->label = self->field;
    self->label_len = self->field_len;
    self->field_len = 0;
    return 0;
}

static int
read_engine(LTSVParser *self)
{
    int i = 0;
    int len = self->val_size;
    for (i = 0; i < len; i++) {
        Engine_read(self->engine, i, *self->val_map[i]);
    }
}

static int
parse_save_field(LTSVParser *self)
{
    const char *colname;
    const char *val;
    int colid;
    int i;
    PyObject *tuple;
    PyObject *label;
    PyObject *field;
    label = PyString_FromStringAndSize(self->label, self->label_len);
    if (label == NULL)
        return -1;
    field = PyString_FromStringAndSize(self->field, self->field_len);
    if (field == NULL)
        return -1;
    tuple = PyTuple_Pack(2, label, field);
    if (tuple == NULL)
        return -1;

    if(!self->engine->is_success){
        colname = PyString_AS_STRING(label);
        val     = PyString_AS_STRING(field);
        colid = ColMap_get(self->colmap, colname);
        if(colid>=0){
            self->val_map[colid] = val;
            ++self->val_len;
            if(self->val_len==self->val_size){
                read_engine(self);
            }
        }
    }
    self->field_len = 0;
    PyList_Append(self->fields, tuple);
    Py_DECREF(tuple);
    Py_DECREF(label);
    Py_DECREF(field);
    self->col += 1;
    return 0;
}

static int
parse_grow_buff(LTSVParser *self)
{
    if (self->field_size == 0) {
        self->field_size = 4096;
        if (self->field != NULL)
            PyMem_Free(self->field);
        self->field = PyMem_Malloc(self->field_size);
        self->label = NULL;
    }
    else {
        if (self->field_size > INT_MAX / 2) {
            PyErr_NoMemory();
            return 0;
        }
        self->field_size *= 2;
        self->field = PyMem_Realloc(self->field, self->field_size);
    }
    if (self->field == NULL) {
        PyErr_NoMemory();
        return 0;
    }
    return 1;
}

static int
parse_add_char(LTSVParser *self, char c)
{
    if (self->field_len >= field_limit) {
        PyErr_Format(ltsv_error_obj, "field larger than field limit (%ld)",
                     field_limit);
        return -1;
    }
    if (self->field_len == self->field_size && !parse_grow_buff(self))
        return -1;
    self->field[self->field_len++] = c;
    return 0;
}

static int
parse_process_char(LTSVParser *self, char c)
{
    switch (self->state) {
    case START_RECORD:
        /* start of record */
        if (c == '\n' || c == '\r') {
            self->state = EAT_CRNL;
            break;
        }
        /* normal character - handle as START_FIELD */
        self->state = START_LABEL;
        /* fallthru */
    case START_LABEL:
        /* expecting field */
        if (c == '\n' || c == '\r') {
            /* save empty field - return [fields] */
            self->state = EAT_CRNL;
        }
        else if (c == ':') {
            /* save empty label */
            if (parse_save_label(self) < 0)
                return -1;
        }
        else if (c == '\t') {
            /* save empty field */
            if (parse_save_field(self) < 0)
                return -1;
        }
        else {
            if (parse_add_char(self, c) < 0)
                return -1;
            self->state = IN_LABEL;
        }
        break;
    case IN_LABEL:
        if (c == '\n' || c == '\r') {
            /* end of line - return [fields] */
            self->state = EAT_CRNL;
        }
        else if (c == ':') {
            /* save field - wait for new field */
            if (parse_save_label(self) < 0)
                return -1;

            self->state = IN_FIELD;
        }
        else {
            /* normal character - save in field */
            if (parse_add_char(self, c) < 0)
                return -1;
        }
        break;
    case IN_FIELD:
        /* in unquoted field */
        if (c == '\n' || c == '\r') {
            /* end of line - return [fields] */
            if (parse_save_field(self) < 0)
                return -1;
            self->state = EAT_CRNL;
        }
        else if (c == '\t') {
            /* save field - wait for new field */
            if (parse_save_field(self) < 0)
                return -1;

            if(self->engine->is_fail)
                self->state = QUERY_FAIL;
            else
                self->state = START_FIELD;
        }
        else {
            /* normal character - save in field */
            if (parse_add_char(self, c) < 0)
                return -1;
        }
        break;
    case EAT_CRNL:
        if (c == '\n' || c == '\r')
            ;
        else if (c == '\0')
            self->state = START_RECORD;
        else {
            PyErr_Format(ltsv_error_obj, "new-line character seen in unquoted field - do you need to open the file in universal-newline mode?");
            return -1;
        }
        break;
    case QUERY_FAIL:
        if (c == '\n' || c == '\r' || c=='\0') {
            self->state = START_RECORD;
        }
        break;
    }
    return 0;
}

static int
parse_reset(LTSVParser *self)
{
    Py_XDECREF(self->fields);
    self->fields = PyList_New(0);
    if (self->fields == NULL)
        return -1;
    self->field_len = 0;
    self->label_len = 0;
    self->state = START_RECORD;
    self->val_len = 0;
    Engine_reset(self->engine);
    self->col = 0;
    return 0;
}

static char *parser_kws[] = {
    "engine",
    "file",
    "colmap",
    "delimiter",
    "quotechar",
    NULL
};

static PyObject *
LTSVParser_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    Engine *engine;
    PyObject *pyfile  = NULL;
    PyObject *map = NULL;
    ColMap *colmap = NULL;
    LTSVParser * self = PyObject_GC_New(LTSVParser, &LTSVParser_Type);
    if (self == NULL){
        return NULL;
    }
    if (!PyArg_ParseTupleAndKeywords(args, kwargs,
                                     "O!OO", parser_kws,
                                     &Engine_Type, &engine,
                                     &pyfile,
                                     &map)){
        return NULL;
    }
    self->engine = engine;
    if(PyFile_Check(pyfile)){
        self->file   = PyFile_AsFile(pyfile);
        self->is_file = 1;
        self->pyfile = pyfile;
    }else{
        self->file    = NULL;
        self->is_file = 0;
        self->pyfile  = PyObject_GetIter(pyfile);
        if (self->pyfile == NULL) {
            PyErr_SetString(PyExc_TypeError,
                            "argument 1 must be an iterator");
            return NULL;
        }
    }
    colmap = ColMap_new(map);
    if (colmap == NULL) {
        PyErr_SetString(PyExc_TypeError,
                        "argument 2 must be an dict");
        return NULL;
    }
    self->val_size = (int)PyDict_Size(map);
    self->valmap = PyMem_Malloc(sizeof(char*) * self->val_size);
    if(self->valmap == NULL){
        return NULL;
    }
    Py_INCREF(pyfile);
    Py_INCREF(engine);
    self->colmap = colmap;
    self->fields = NULL;
    self->field  = NULL;
    self->label  = NULL;
    self->field_size = 0;
    self->line_num   = 0;
    if (parse_reset(self) < 0) {
        Py_DECREF(pyfile);
        Py_DECREF(engine);
        return NULL;
    }
    PyObject_GC_Track(self);
    return (PyObject *)self;
}

static PyObject *
LTSVParser_iternext_filelike(LTSVParser *self)
{
    char *buf;
    char c;
    PyObject *fields = NULL;
    PyObject *lineobj = NULL;
    long i;
    long linelen;
    Engine_reset(self->engine);
    while(!self->engine->is_success){
        if (parse_reset(self) < 0)
            return NULL;
        do {
            lineobj = PyIter_Next(self->pyfile);
            if (lineobj == NULL) {
                /* End of input OR exception */
                if (!PyErr_Occurred() && (self->field_len != 0 ||
                                          self->state == IN_QUOTED_FIELD)) {
                    if (parse_save_field(self) >= 0 )
                        break;
                }
                return NULL;
            }
            ++self->line_num;

            buf = PyString_AsString(lineobj);
            linelen = PyString_Size(lineobj);

            if (buf == NULL || linelen < 0) {
                return NULL;
            }
            for(i=0; i<linelen; ++i){
                c = buf[i];
                if (c == '\0') {
                    Py_DECREF(lineobj);
                    PyErr_Format(ltsv_error_obj,
                                 "line contains NULL byte");
                    goto err;
                }
                if (parse_process_char(self, c) < 0) {
                    Py_DECREF(lineobj);
                    goto err;
                }
                if (self->state == QUERY_FAIL)
                    break;
            }
            Py_DECREF(lineobj);
        } while (self->state != EAT_CRNL);
    }
    fields = self->fields;
    self->fields = NULL;
err:
    return fields;
}

#define MAXBUFSIZE 30000
static PyObject *
LTSVParser_iternext(LTSVParser *self)
{
    if(!self->is_file)
        return LTSVParser_iternext_filelike(self);
    char buf[MAXBUFSIZE];
    char c;
    char *cp;
    PyObject *fields = NULL;
    long i;
    long linelen;
    Engine_reset(self->engine);
    while(!self->engine->is_success){
        if (parse_reset(self) < 0)
            return NULL;
        do {
            PyFile_IncUseCount((PyFileObject*)self->pyfile);
            Py_BEGIN_ALLOW_THREADS
            cp = fgets(buf, MAXBUFSIZE, self->file);
            Py_END_ALLOW_THREADS
            PyFile_DecUseCount((PyFileObject*)self->pyfile);
            if (cp == NULL) {
                /* End of input OR exception */
                if (!PyErr_Occurred() && (self->field_len != 0 ||
                                          self->state == IN_QUOTED_FIELD)) {
                    if (parse_save_field(self) >= 0 )
                        break;
                }
                return NULL;
            }
            ++self->line_num;
            linelen = strlen(buf);
            if (buf == NULL || linelen < 0) {
                return NULL;
            }
            for(i=0; i<linelen; ++i){
                c = buf[i];
                if (c == '\0') {
                    PyErr_Format(ltsv_error_obj,
                                 "line contains NULL byte");
                    goto err;
                }
                if (parse_process_char(self, c) < 0) {
                    goto err;
                }
                if (self->state == QUERY_FAIL)
                    break;
            }
        } while (self->state != EAT_CRNL);
    }
    fields = self->fields;
    self->fields = NULL;
err:
    return fields;
}

static void
LTSVParser_dealloc(LTSVParser *self)
{
    PyObject_GC_UnTrack(self);
    Py_XDECREF(self->pyfile);
    Py_XDECREF(self->engine);
    Py_XDECREF(self->fields);
    if (self->field != NULL)
        PyMem_Free(self->field);

    ColMap_dealloc(self->colmap);
    PyObject_GC_Del(self);
}

static int
LTSVParser_traverse(LTSVParser *self, visitproc visit, void *arg)
{
    Py_VISIT(self->pyfile);
    Py_VISIT(self->fields);
    Py_VISIT(self->engine);
    return 0;
}

static int
LTSVParser_clear(LTSVParser *self)
{
    Py_CLEAR(self->pyfile);
    Py_CLEAR(self->fields);
    Py_CLEAR(self->engine);
    return 0;
}

PyDoc_STRVAR(LTSVParser_Type_doc,
"LTSV reader\n"
"\n"
"LTSVParser objects are responsible for reading and parsing tabular data\n"
"in LTSV format.\n"
);

static struct PyMethodDef LTSVParser_methods[] = {
    { NULL, NULL }
};
#define R_OFF(x) offsetof(LTSVParser, x)

static struct PyMemberDef LTSVParser_memberlist[] = {
    { "engine", T_ULONG, R_OFF(engine), RO },
    { "pyfile", T_ULONG, R_OFF(pyfile), RO },
    { "fields", T_ULONG, R_OFF(fields), RO },
    { "line_num", T_ULONG, R_OFF(line_num), RO },
    { NULL }
};


static PyTypeObject LTSVParser_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "engine.LTSVParser",                     /*tp_name*/
    sizeof(LTSVParser),                      /*tp_basicsize*/
    0,                                      /*tp_itemsize*/
    /* methods */
    (destructor)LTSVParser_dealloc,             /*tp_dealloc*/
    (printfunc)0,                           /*tp_print*/
    (getattrfunc)0,                         /*tp_getattr*/
    (setattrfunc)0,                         /*tp_setattr*/
    (cmpfunc)0,                             /*tp_compare*/
    (reprfunc)0,                            /*tp_repr*/
    0,                                      /*tp_as_number*/
    0,                                      /*tp_as_sequence*/
    0,                                      /*tp_as_mapping*/
    (hashfunc)0,                            /*tp_hash*/
    (ternaryfunc)0,                         /*tp_call*/
    (reprfunc)0,                                /*tp_str*/
    0,                                      /*tp_getattro*/
    0,                                      /*tp_setattro*/
    0,                                      /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE |
        Py_TPFLAGS_HAVE_GC,                     /*tp_flags*/
    LTSVParser_Type_doc,                        /*tp_doc*/
    (traverseproc)LTSVParser_traverse,          /*tp_traverse*/
    (inquiry)LTSVParser_clear,                  /*tp_clear*/
    0,                                      /*tp_richcompare*/
    0,                                      /*tp_weaklistoffset*/
    PyObject_SelfIter,                          /*tp_iter*/
    (getiterfunc)LTSVParser_iternext,           /*tp_iternext*/
    LTSVParser_methods,                         /*tp_methods*/
    LTSVParser_memberlist,                      /*tp_members*/
    0,                                      /*tp_getset*/
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    0,               /* tp_init */
    0,                         /* tp_alloc */
    LTSVParser_new,                /* tp_new */
};

int
register_ltsv(PyObject *module)
{
    if (PyType_Ready(&LTSVParser_Type) < 0)
        return -1;

    Py_INCREF(&LTSVParser_Type);
    if (PyModule_AddObject(module, "LTSVParser", (PyObject *)&LTSVParser_Type))
        return -1;

    /* Add the LTSV exception object to the module. */
    ltsv_error_obj = PyErr_NewException("engine.LTSVError", NULL, NULL);
    if (ltsv_error_obj == NULL)
        return -1;

    PyModule_AddObject(module, "LTSVError", ltsv_error_obj);
    return 1;
}

/*
 * LTSVParser End
 **/

