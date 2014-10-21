#include <Python.h>
#include <structmember.h>

#include "engine.h"
#include "csv.h"
#include "colmap.h"

/**
 * CSVParser
 */

typedef enum {
    START_RECORD, START_FIELD, IN_FIELD,
    IN_QUOTED_FIELD, QUOTE_IN_QUOTED_FIELD,
    QUERY_FAIL
} ParserState;

typedef struct {
    PyObject_HEAD

    Engine *engine;
    ColMap *colmap;
    PyObject *pyfile;
    FILE *file;
    PyObject *fields;           /* field list for current record */
    ParserState state;          /* current CSV parse state */
    char *field;                /* build current field in here */
    int field_size;             /* size of allocated buffer */
    int field_len;              /* length of current field */
    int col;
    int is_file;
    unsigned long line_num;     /* Source-file line number */
    char delimiter;
    char quotechar;
} CSVParser;

static PyObject *csv_error_obj;     /* CSV exception */
static long field_limit = 128 * 1024;   /* max parsed field size */


staticforward PyTypeObject CSVParser_Type;

#define CSVParser_Check(v)   (Py_TYPE(v) == &CSVParser_Type)

static int
parse_save_field(CSVParser *self)
{
    const char *string;
    int colid;
    PyObject *field;
    field = PyString_FromStringAndSize(self->field, self->field_len);
    if (field == NULL)
        return -1;

    if(!self->engine->is_success){
        string = PyString_AS_STRING(field);
        colid = ColMap_get_int(self->colmap, self->col);
        if(colid>=0){
            Logq_Engine_read(self->engine, colid, string);
        }
    }
    self->field_len = 0;
    PyList_Append(self->fields, field);
    Py_DECREF(field);
    self->col += 1;
    return 0;
}

static int
parse_grow_buff(CSVParser *self)
{
    if (self->field_size == 0) {
        self->field_size = 4096;
        if (self->field != NULL)
            PyMem_Free(self->field);
        self->field = PyMem_Malloc(self->field_size);
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
parse_add_char(CSVParser *self, char c)
{
    if (self->field_len >= field_limit) {
        PyErr_Format(csv_error_obj, "field larger than field limit (%ld)",
                     field_limit);
        return -1;
    }
    if (self->field_len == self->field_size && !parse_grow_buff(self))
        return -1;
    self->field[self->field_len++] = c;
    return 0;
}

static int
parse_process_char(CSVParser *self, char c)
{
    switch (self->state) {
    case START_RECORD:
        /* start of record */
        if (c == '\n' || c == '\r') {
            self->state = START_RECORD;
            break;
        }
        /* normal character - handle as START_FIELD */
        self->state = START_FIELD;
        /* fallthru */
    case START_FIELD:
        /* expecting field */
        if (c == '\n' || c == '\r') {
            /* save empty field - return [fields] */
            if (parse_save_field(self) < 0)
                return -1;
            self->state = START_RECORD;
        }
        else if (c == self->quotechar) {
            /* start quoted field */
            self->state = IN_QUOTED_FIELD;
        }
        else if (c == self->delimiter) {
            /* save empty field */
            if (parse_save_field(self) < 0)
                return -1;

        }
        else {
            if (parse_add_char(self, c) < 0)
                return -1;
            self->state = IN_FIELD;
        }
        break;

    case IN_FIELD:
        /* in unquoted field */
        if (c == '\n' || c == '\r') {
            /* end of line - return [fields] */
            if (parse_save_field(self) < 0)
                return -1;
            self->state = START_RECORD;
        }
        else if (c == self->delimiter) {
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

    case IN_QUOTED_FIELD:
        /* in quoted field */
        if (c == self->quotechar) {
            /* doublequote; " represented by "" */
            self->state = QUOTE_IN_QUOTED_FIELD;
        }
        else {
            /* normal character - save in field */
            if (parse_add_char(self, c) < 0)
                return -1;
        }
        break;

    case QUOTE_IN_QUOTED_FIELD:
        /* doublequote - seen a quote in an quoted field */
        if (c == self->quotechar) {
            /* save "" as " */
            if (parse_add_char(self, c) < 0)
                return -1;
            self->state = IN_QUOTED_FIELD;
        }
        else if (c == self->delimiter) {
            /* save field - wait for new field */
            if (parse_save_field(self) < 0)
                return -1;

            self->state = START_FIELD;
        }
        else if (c == '\n' || c == '\r') {
            /* end of line - return [fields] */
            if (parse_save_field(self) < 0)
                return -1;

            if(self->engine->is_fail)
                self->state = QUERY_FAIL;
            else
                self->state = START_FIELD;
        }else{
            if(parse_add_char(self, c) < 0)
                return -1;

            self->state = IN_FIELD;
        }
        break;

    case QUERY_FAIL:
        if (c == '\n' || c == '\r') {
            self->state = START_RECORD;
        }
        break;
    }
    return 0;
}

static int
parse_reset(CSVParser *self)
{
    Py_XDECREF(self->fields);
    self->fields = PyList_New(0);
    if (self->fields == NULL)
        return -1;
    self->field_len = 0;
    self->state = START_RECORD;
    Logq_Engine_reset(self->engine);
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
CSVParser_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    Engine *engine;
    PyObject *pyfile  = NULL;
    PyObject *map = NULL;
    ColMap *colmap = NULL;
    char delimiter = ',';
    char quotechar = '"';
    CSVParser * self = PyObject_GC_New(CSVParser, &CSVParser_Type);
    if (self == NULL){
        return NULL;
    }
    if (!PyArg_ParseTupleAndKeywords(args, kwargs,
                                     "O!OO|cc", parser_kws,
                                     &Logq_Engine_Type, &engine,
                                     &pyfile,
                                     &map,
                                     &delimiter, &quotechar)){
        return NULL;
    }
    Py_INCREF(pyfile);
    Py_INCREF(engine);
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
    if(!PySequence_Check(map)){
        PyErr_SetString(PyExc_TypeError,
                        "argument 2 must be a list");
        return NULL;
    }
    colmap = ColMap_new(map);
    if (colmap == NULL) {
        PyErr_SetString(PyExc_TypeError,
                        "argument 2 must be a list");
        return NULL;
    }
    self->colmap = colmap;
    self->fields = NULL;
    self->field  = NULL;
    self->field_size = 0;
    self->line_num   = 0;
    self->delimiter = delimiter;
    self->quotechar = quotechar;
    if (parse_reset(self) < 0) {
        Py_DECREF(pyfile);
        Py_DECREF(engine);
        Py_DECREF(self);
        return NULL;
    }
    PyObject_GC_Track(self);
    return (PyObject *)self;
}

static PyObject *
CSVParser_iternext_filelike(CSVParser *self)
{
    char *buf;
    char c;
    PyObject *fields = NULL;
    PyObject *lineobj = NULL;
    long i;
    long linelen;
    Logq_Engine_reset(self->engine);
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
                    PyErr_Format(csv_error_obj,
                                 "line contains NULL byte");
                    goto err;
                }
                if (parse_process_char(self, c) < 0) {
                    Py_DECREF(lineobj);
                    goto err;
                }
                //query fail. go next line
                if (self->state == QUERY_FAIL){
                    if(buf[linelen-1]=='\n'){
                        self->state = START_RECORD;
                    }
                    break;
                }
            }
            Py_DECREF(lineobj);
        } while (self->state != START_RECORD);
    }
    fields = self->fields;
    self->fields = NULL;
err:
    return fields;
}

#define MAXBUFSIZE 30000
static PyObject *
CSVParser_iternext(CSVParser *self)
{
    if(!self->is_file)
        return CSVParser_iternext_filelike(self);
    char buf[MAXBUFSIZE];
    char c;
    char *cp;
    PyObject *fields = NULL;
    long i;
    long linelen;
    Logq_Engine_reset(self->engine);
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
                    PyErr_Format(csv_error_obj,
                                 "line contains NULL byte");
                    goto err;
                }
                if (parse_process_char(self, c) < 0) {
                    goto err;
                }
                //query fail. go next line
                if (self->state == QUERY_FAIL){
                    if(buf[linelen-1]=='\n'){
                        self->state = START_RECORD;
                    }
                    break;
                }
            }
        } while (self->state != START_RECORD);
    }
    fields = self->fields;
    self->fields = NULL;
err:
    return fields;
}

static void
CSVParser_dealloc(CSVParser *self)
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
CSVParser_traverse(CSVParser *self, visitproc visit, void *arg)
{
    Py_VISIT(self->pyfile);
    Py_VISIT(self->fields);
    Py_VISIT(self->engine);
    return 0;
}

static int
CSVParser_clear(CSVParser *self)
{
    Py_CLEAR(self->pyfile);
    Py_CLEAR(self->fields);
    Py_CLEAR(self->engine);
    return 0;
}

PyDoc_STRVAR(CSVParser_Type_doc,
"CSV reader\n"
"\n"
"CSVParser objects are responsible for reading and parsing tabular data\n"
"in CSV format.\n"
);

static struct PyMethodDef CSVParser_methods[] = {
    { NULL, NULL }
};
#define R_OFF(x) offsetof(CSVParser, x)

static struct PyMemberDef CSVParser_memberlist[] = {
    { "engine", T_ULONG, R_OFF(engine), RO },
    { "pyfile", T_ULONG, R_OFF(pyfile), RO },
    { "fields", T_ULONG, R_OFF(fields), RO },
    { "line_num", T_ULONG, R_OFF(line_num), RO },
    { NULL }
};


static PyTypeObject CSVParser_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "engine.CSVParser",                     /*tp_name*/
    sizeof(CSVParser),                      /*tp_basicsize*/
    0,                                      /*tp_itemsize*/
    /* methods */
    (destructor)CSVParser_dealloc,             /*tp_dealloc*/
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
    CSVParser_Type_doc,                        /*tp_doc*/
    (traverseproc)CSVParser_traverse,          /*tp_traverse*/
    (inquiry)CSVParser_clear,                  /*tp_clear*/
    0,                                      /*tp_richcompare*/
    0,                                      /*tp_weaklistoffset*/
    PyObject_SelfIter,                          /*tp_iter*/
    (getiterfunc)CSVParser_iternext,           /*tp_iternext*/
    CSVParser_methods,                         /*tp_methods*/
    CSVParser_memberlist,                      /*tp_members*/
    0,                                      /*tp_getset*/
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    0,               /* tp_init */
    0,                         /* tp_alloc */
    CSVParser_new,                /* tp_new */
};

int
Logq_register_csv(PyObject *module)
{
    if (PyType_Ready(&CSVParser_Type) < 0)
        return -1;

    Py_INCREF(&CSVParser_Type);
    if (PyModule_AddObject(module, "CSVParser", (PyObject *)&CSVParser_Type))
        return -1;

    /* Add the CSV exception object to the module. */
    csv_error_obj = PyErr_NewException("engine.CSVError", NULL, NULL);
    if (csv_error_obj == NULL)
        return -1;

    PyModule_AddObject(module, "CSVError", csv_error_obj);
    return 1;
}

/*
 * CSVParser End
 **/

