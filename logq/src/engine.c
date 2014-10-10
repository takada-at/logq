#define MODULE_VERSION "0.0.1"

#define STR_EQ 1

#include <Python.h>
#include <structmember.h>

#include "engine.h"

/**
 * Engine
 */
static PyTypeObject Engine_Type;

typedef struct {
    int op;
    char *arg;
} Expr;

typedef struct {
    PyObject_HEAD

    int start;
    int success;
    int fail;
    int state;
    int is_success;
    int is_fail;
    int colsize;
    int statesize;
    int exprsize;
    int *expr_table;
    int *success_table;
    int *fail_table;
    Expr *exprs;
} Engine;

static void
Engine_dealloc(Engine* self)
{
    int i;
    Expr *tmp;
    for(i=1; i<self->exprsize; ++i){
        tmp = self->exprs + i;
        PyMem_Free(tmp->arg);
    }
    PyMem_Free(self->exprs);
    PyMem_Free(self->expr_table);
    PyMem_Free(self->success_table);
    PyMem_Free(self->fail_table);
    self->ob_type->tp_free((PyObject*)self);
}

static char *engine_kws[] = {
    "start",
    "success",
    "fail",
    "exprs",
    "expr_table",
    "success_table",
    "fail_table",
    NULL
};

static int op2int(const char *op){
    if(strcmp(op, "=")==0)
        return STR_EQ;

    return 0;
}

static PyObject *
Engine_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    Engine *self;

    self = (Engine *)type->tp_alloc(type, 0);
    if (self == NULL){
        return NULL;
    }

    return (PyObject *)self;
}

static int
construct_expr(Expr *exprs, PyObject *pyexpr)
{
    int argsize;
    const char *py_op;
    const char *py_arg;
    char *arg;
    Expr expr;
    if(!PyArg_ParseTuple(pyexpr, "ss", &py_op, &py_arg))
        return 0;

    argsize = (int)strlen(py_arg) + 1;
    arg  = PyMem_Malloc(sizeof(char) * argsize);
    if(arg==NULL)
        return 0;

    strcpy(arg, py_arg);
    expr.op = op2int(py_op);
    expr.arg = arg;
    *exprs = expr;
    return 1;
}

static int
Engine_init(Engine *self, PyObject *args, PyObject *kwargs)
{
    int start;
    int success;
    int fail;
    int colsize;
    int statesize;
    int exprsize;
    int i = 0;
    int j = 0;
    PyObject *py_exprs = NULL;
    PyObject *py_expr_table = NULL;
    PyObject *py_success_table = NULL;
    PyObject *py_fail_table = NULL;
    PyObject *py_expr = NULL;
    Expr *exprs = NULL;
    int *expr_table = NULL;
    int *success_table = NULL;
    int *fail_table = NULL;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs,
                                     "iiiOOOO", engine_kws,
                                     &start,
                                     &success,
                                     &fail,
                                     &py_exprs,
                                     &py_expr_table,
                                     &py_success_table,
                                     &py_fail_table))
        return -1;

    colsize       = (int)PyList_Size(PyList_GetItem(py_expr_table, 0));
    statesize     = (int)PyList_Size(py_expr_table);
    exprsize      = (int)PyList_Size(py_exprs);
    exprs         = PyMem_Malloc( sizeof(Expr) * exprsize );
    expr_table    = PyMem_Malloc( sizeof(int) * statesize * colsize);
    success_table = PyMem_Malloc( sizeof(int) * statesize * colsize);
    fail_table    = PyMem_Malloc( sizeof(int) * statesize * colsize);
    if(exprs == NULL || expr_table == NULL || success_table == NULL
       || fail_table == NULL)
        return -1;

    for(i=1; i<exprsize; ++i){
        py_expr = PyList_GetItem(py_exprs, i);
        if(!PyTuple_Check(py_expr))
            return -1;

        if(construct_expr(exprs+i, py_expr)==0)
            return -1;
    }
    for(i=0; i<statesize; ++i){
        for(j=0; j<colsize; ++j){
            expr_table[i*colsize + j]    = (int)PyInt_AsLong(PyList_GetItem(PyList_GetItem(py_expr_table, i), j));
            success_table[i*colsize + j] = (int)PyInt_AsLong(PyList_GetItem(PyList_GetItem(py_success_table, i), j));
            fail_table[i*colsize + j]    = (int)PyInt_AsLong(PyList_GetItem(PyList_GetItem(py_fail_table, i), j));
        }
    }
    self->start      = start;
    self->state      = start;
    self->is_success = 0;
    self->is_fail    = 0;
    self->success   = success;
    self->fail      = fail;
    self->colsize   = colsize;
    self->statesize = statesize;
    self->exprsize  = exprsize;
    self->expr_table    = expr_table;
    self->success_table = success_table;
    self->fail_table    = fail_table;
    self->exprs         = exprs;
    return 0;
}

static int execute_expr(Expr *expr, const char *val)
{
    switch(expr->op){
    case STR_EQ:
        if(strcmp(expr->arg, val) == 0){
            return 1;
        }else
            return 0;
        break;
    }
    return 0;
}

int
Engine_read(Engine *self, int col, const char* val){
    Expr *expr;
    int expr_id;
    while(1){
        expr_id = self->expr_table[(self->state) * (self->colsize) + col];
        if(expr_id){
            expr = self->exprs + expr_id;
            if(execute_expr(expr, val)){
                self->state      = self->success_table[(self->state) * (self->colsize) + col];
                self->is_success = self->state==self->success;
            }else{
                self->state   = self->fail_table[(self->state) * (self->colsize) + col];
                self->is_fail = self->state==self->fail;
            }
        }else{
            break;
        }
    }
    return 1;
}

static PyObject *
Engine_transition(Engine* self, PyObject *args)
{
    int col;
    const char *val;
    if (!PyArg_ParseTuple(args, "is", &col, &val))
        return NULL;

    Engine_read(self, col, val);
    Py_RETURN_NONE;
}

PyObject *
Engine_reset(Engine *self){
    self->is_success = 0;
    self->is_fail = 0;
    self->state = self->start;
    Py_RETURN_NONE;
}

static PyMemberDef Engine_members[] = {
    {"state",   T_INT, offsetof(Engine, state), READONLY },
    {"start",   T_INT, offsetof(Engine, start), READONLY },
    {"success", T_INT, offsetof(Engine, success), READONLY },
    {"fail",    T_INT, offsetof(Engine, fail), READONLY },
    {"is_success",   T_INT, offsetof(Engine, is_success), READONLY },
    {"is_fail",   T_INT, offsetof(Engine, is_fail), READONLY },
    {NULL}
};

static struct PyMethodDef Engine_methods[] = {
    {"transition", (PyCFunction)Engine_transition, METH_VARARGS,
     "Engine transition"
    },
    {"reset", (PyCFunction)Engine_reset, METH_NOARGS,
     "Engine reset"
    },
    {NULL}
};

static PyTypeObject Engine_Type = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "engine.Engine",           /*tp_name*/
    sizeof(Engine),            /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)Engine_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "Engine",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    Engine_methods,            /* tp_methods */
    Engine_members,            /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Engine_init,               /* tp_init */
    0,                         /* tp_alloc */
    Engine_new,                /* tp_new */
};

PyDoc_STRVAR(engine_module_doc,
             "");

static PyMethodDef engine_methods[] = {
    { NULL }
};

int
register_engine(PyObject *module)
{
    if (PyType_Ready(&Engine_Type) < 0)
        return -1;

    Py_INCREF(&Engine_Type);
    if (PyModule_AddObject(module, "Engine", (PyObject *)&Engine_Type))
        return -1;

    return 1;
}
/*
 * Engine End
 **/

/**
 * CSVParser
 */

typedef enum {
    START_RECORD, START_FIELD, IN_FIELD,
    IN_QUOTED_FIELD, QUOTE_IN_QUOTED_FIELD,
    EAT_CRNL, QUERY_FAIL, QUERY_FAIL_EAT_CRNL
} ParserState;

typedef struct {
    PyObject_HEAD

    Engine *engine;
    PyObject *pyfile;
    FILE *file;
    PyObject *fields;           /* field list for current record */
    ParserState state;          /* current CSV parse state */
    char *field;                /* build current field in here */
    int field_size;             /* size of allocated buffer */
    int field_len;              /* length of current field */
    int col;
    unsigned long line_num;     /* Source-file line number */
    char delimiter;
    char quotechar;
} CSVParser;

static PyObject *csv_error_obj;     /* CSV exception */
static long field_limit = 128 * 1024;   /* max parsed field size */


staticforward PyTypeObject CSVParser_Type;

#define CSVParser_Check(v)   (Py_TYPE(v) == &CSVParser_Type)

static char *reader_kws[] = {
    "engine",
    "file",
    "delimiter",
    "quotechar",
    NULL
};

static int
parse_save_field(CSVParser *self)
{
    const char *string;
    PyObject *field;
    field = PyString_FromStringAndSize(self->field, self->field_len);
    if (field == NULL)
        return -1;

    if(!self->engine->is_success){
        string = PyString_AS_STRING(field);
        Engine_read(self->engine, self->col, string);
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
        if (c == '\0')
            /* empty line - return [] */
            break;
        else if (c == '\n' || c == '\r') {
            self->state = EAT_CRNL;
            break;
        }
        /* normal character - handle as START_FIELD */
        self->state = START_FIELD;
        /* fallthru */
    case START_FIELD:
        /* expecting field */
        if (c == '\n' || c == '\r' || c == '\0') {
            /* save empty field - return [fields] */
            if (parse_save_field(self) < 0)
                return -1;
            self->state = (c == '\0' ? START_RECORD : EAT_CRNL);
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
        if (c == '\n' || c == '\r' || c == '\0') {
            /* end of line - return [fields] */
            if (parse_save_field(self) < 0)
                return -1;
            self->state = (c == '\0' ? START_RECORD : EAT_CRNL);
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
        if (c == '\0')
            ;
        else if (c == self->quotechar) {
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
        else if (c == '\n' || c == '\r' || c == '\0') {
            /* end of line - return [fields] */
            if (parse_save_field(self) < 0)
                return -1;

            if(self->engine->is_fail)
                self->state = QUERY_FAIL;
            else
                self->state = START_FIELD;
        }
        if (parse_add_char(self, c) < 0)
            return -1;
        self->state = IN_FIELD;
        break;

    case EAT_CRNL:
        if (c == '\n' || c == '\r')
            ;
        else if (c == '\0')
            self->state = START_RECORD;
        else {
            PyErr_Format(csv_error_obj, "new-line character seen in unquoted field - do you need to open the file in universal-newline mode?");
            return -1;
        }
        break;

    case QUERY_FAIL:
        if (c == '\n' || c == '\r') {
            self->state = QUERY_FAIL_EAT_CRNL;
        }
        break;

    case QUERY_FAIL_EAT_CRNL:
        if (c == '\n' || c == '\r')
            ;
        else if (c == '\0') 
            self->state = START_RECORD;
        else {
            return -1;
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
    Engine_reset(self->engine);
    self->col = 0;
    return 0;
}

static PyObject *
CSVParser_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    Engine *engine;
    PyObject *pyfile  = NULL;
    FILE *file = NULL;
    char delimiter;
    char quotechar;
    CSVParser * self = PyObject_GC_New(CSVParser, &CSVParser_Type);

    if (self == NULL){
        return NULL;
    }

    if (!PyArg_ParseTupleAndKeywords(args, kwargs,
                                     "O!Occ", reader_kws,
                                     &Engine_Type, &engine,
                                     &pyfile,
                                     &delimiter, &quotechar)){
        Py_DECREF(self);
        return NULL;
    }
    if(!PyFile_Check(pyfile)){
        Py_DECREF(self);
        return NULL;
    }
    file = PyFile_AsFile(pyfile);
    PyFile_IncUseCount((PyFileObject *)pyfile);
    Py_INCREF(pyfile);
    Py_INCREF(engine);
    self->engine = engine;
    self->pyfile = pyfile;
    self->file   = file;
    self->fields = NULL;
    self->field  = NULL;
    self->field_size = 0;
    self->line_num   = 0;
    self->delimiter = delimiter;
    self->quotechar = quotechar;
    if (parse_reset(self) < 0) {
        PyFile_DecUseCount((PyFileObject *)pyfile);
        Py_DECREF(pyfile);
        Py_DECREF(engine);
        Py_DECREF(self);
        return NULL;
    }
    PyObject_GC_Track(self);
    return (PyObject *)self;
}

static PyObject *
CSVParser_iternext(CSVParser *self)
{
#define MAXBUFSIZE 300
    char buf[MAXBUFSIZE];
    char c;
    char *cp;
    PyObject *fields = NULL;
    long i;
    long linelen;
    if (parse_reset(self) < 0)
        return NULL;
    do {
        Py_BEGIN_ALLOW_THREADS
        cp = fgets(buf, MAXBUFSIZE, self->file);
        Py_END_ALLOW_THREADS
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
        }
        if (parse_process_char(self, 0) < 0)
            goto err;
    } while (self->state != START_RECORD);

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
    PyFile_DecUseCount((PyFileObject *)self->pyfile);
    if (self->field != NULL)
        PyMem_Free(self->field);

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
    "_csv.reader",                          /*tp_name*/
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
register_csv(PyObject *module)
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


#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initengine(void)
{
    PyObject *module;
    module = Py_InitModule3("engine", engine_methods, engine_module_doc);
    if (module == NULL)
        return;

    if (PyModule_AddStringConstant(module, "__version__",
                                   MODULE_VERSION) == -1)
        return;

    register_engine(module);
    register_csv(module);
}
