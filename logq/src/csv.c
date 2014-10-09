/* csv module */

#define MODULE_VERSION "0.0.1"

#include "Python.h"
#include "structmember.h"

#include "engine.h"

static PyObject *error_obj;     /* CSV exception */
static PyObject *dialects;      /* Dialect registry */
static long field_limit = 128 * 1024;   /* max parsed field size */

typedef enum {
    START_RECORD, START_FIELD, ESCAPED_CHAR, IN_FIELD,
    IN_QUOTED_FIELD, ESCAPE_IN_QUOTED_FIELD, QUOTE_IN_QUOTED_FIELD,
    EAT_CRNL
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
    int numeric_field;          /* treat field as numeric */
    unsigned long line_num;     /* Source-file line number */
    char delimiter;
    char quotechar;
} ReaderObj;

staticforward PyTypeObject Reader_Type;

#define ReaderObject_Check(v)   (Py_TYPE(v) == &Reader_Type)

static char *reader_kws[] = {
    "engine",
    "file",
    "delimiter",
    "quotechar",
    NULL
};

static PyObject *
Reader_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    ReaderObj * self = PyObject_GC_New(ReaderObj, &Reader_Type);
    if (self == NULL){
        return NULL;
    }

    EngineType *etype = NULL;
    Engine *engine = NULL;
    PyObject *pyfile = NULL;
    FILE *file = NULL;
    char delimiter;
    char quotechar;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs,
                                     "O!Occ", reader_kws,
                                     &etype, &engine,
                                     &pyfile,
                                     &delimiter, &quotechar))
        Py_DECREF(self);
        return NULL;

    if(!PyFile_Check(pyfile))
        Py_DECREF(self);
        return NULL;

    FILE *fp = PyFile_AsFile(pyfile);
    PyFile_IncUseCount(pyfile);
    Py_INCREF(pyfile);
    self->engine = engine;
    self->pyfile   = pyfile;
    self->file     = file;
    self->fields = NULL;
    self->field = NULL;
    self->field_size = 0;
    self->line_num = 0;
    self->delimiter = delimiter;
    self->quotechar = quotechar;
    if (parse_reset(self) < 0) {
        PyFile_DecUseCount(pyfile);
        Py_DECREF(pyfile);
        Py_DECREF(self);
        return NULL;
    }
    PyObject_GC_Track(self);
    return (PyObject *)self;
}

static int
parse_save_field(ReaderObj *self)
{
    PyObject *field;

    field = PyString_FromStringAndSize(self->field, self->field_len);
    if (field == NULL)
        return -1;
    self->field_len = 0;
    if (self->numeric_field) {
        PyObject *tmp;

        self->numeric_field = 0;
        tmp = PyNumber_Float(field);
        if (tmp == NULL) {
            Py_DECREF(field);
            return -1;
        }
        Py_DECREF(field);
        field = tmp;
    }
    PyList_Append(self->fields, field);
    Py_DECREF(field);
    return 0;
}

static int
parse_grow_buff(ReaderObj *self)
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
parse_add_char(ReaderObj *self, char c)
{
    if (self->field_len >= field_limit) {
        PyErr_Format(error_obj, "field larger than field limit (%ld)",
                     field_limit);
        return -1;
    }
    if (self->field_len == self->field_size && !parse_grow_buff(self))
        return -1;
    self->field[self->field_len++] = c;
    return 0;
}

static int
parse_process_char(ReaderObj *self, char c)
{
    DialectObj *dialect = self->dialect;

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
        else if (c == dialect->quotechar &&
                 dialect->quoting != QUOTE_NONE) {
            /* start quoted field */
            self->state = IN_QUOTED_FIELD;
        }
        else if (c == dialect->escapechar) {
            /* possible escaped character */
            self->state = ESCAPED_CHAR;
        }
        else if (c == ' ' && dialect->skipinitialspace)
            /* ignore space at start of field */
            ;
        else if (c == dialect->delimiter) {
            /* save empty field */
            if (parse_save_field(self) < 0)
                return -1;
        }
        else {
            /* begin new unquoted field */
            if (dialect->quoting == QUOTE_NONNUMERIC)
                self->numeric_field = 1;
            if (parse_add_char(self, c) < 0)
                return -1;
            self->state = IN_FIELD;
        }
        break;

    case ESCAPED_CHAR:
        if (c == '\0')
            c = '\n';
        if (parse_add_char(self, c) < 0)
            return -1;
        self->state = IN_FIELD;
        break;

    case IN_FIELD:
        /* in unquoted field */
        if (c == '\n' || c == '\r' || c == '\0') {
            /* end of line - return [fields] */
            if (parse_save_field(self) < 0)
                return -1;
            self->state = (c == '\0' ? START_RECORD : EAT_CRNL);
        }
        else if (c == dialect->escapechar) {
            /* possible escaped character */
            self->state = ESCAPED_CHAR;
        }
        else if (c == dialect->delimiter) {
            /* save field - wait for new field */
            if (parse_save_field(self) < 0)
                return -1;
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
        else if (c == dialect->escapechar) {
            /* Possible escape character */
            self->state = ESCAPE_IN_QUOTED_FIELD;
        }
        else if (c == dialect->quotechar &&
                 dialect->quoting != QUOTE_NONE) {
            if (dialect->doublequote) {
                /* doublequote; " represented by "" */
                self->state = QUOTE_IN_QUOTED_FIELD;
            }
            else {
                /* end of quote part of field */
                self->state = IN_FIELD;
            }
        }
        else {
            /* normal character - save in field */
            if (parse_add_char(self, c) < 0)
                return -1;
        }
        break;

    case ESCAPE_IN_QUOTED_FIELD:
        if (c == '\0')
            c = '\n';
        if (parse_add_char(self, c) < 0)
            return -1;
        self->state = IN_QUOTED_FIELD;
        break;

    case QUOTE_IN_QUOTED_FIELD:
        /* doublequote - seen a quote in an quoted field */
        if (dialect->quoting != QUOTE_NONE &&
            c == dialect->quotechar) {
            /* save "" as " */
            if (parse_add_char(self, c) < 0)
                return -1;
            self->state = IN_QUOTED_FIELD;
        }
        else if (c == dialect->delimiter) {
            /* save field - wait for new field */
            if (parse_save_field(self) < 0)
                return -1;
            self->state = START_FIELD;
        }
        else if (c == '\n' || c == '\r' || c == '\0') {
            /* end of line - return [fields] */
            if (parse_save_field(self) < 0)
                return -1;
            self->state = (c == '\0' ? START_RECORD : EAT_CRNL);
        }
        else if (!dialect->strict) {
            if (parse_add_char(self, c) < 0)
                return -1;
            self->state = IN_FIELD;
        }
        else {
            /* illegal */
            PyErr_Format(error_obj, "'%c' expected after '%c'",
                            dialect->delimiter,
                            dialect->quotechar);
            return -1;
        }
        break;

    case EAT_CRNL:
        if (c == '\n' || c == '\r')
            ;
        else if (c == '\0')
            self->state = START_RECORD;
        else {
            PyErr_Format(error_obj, "new-line character seen in unquoted field - do you need to open the file in universal-newline mode?");
            return -1;
        }
        break;

    }
    return 0;
}

static int
parse_reset(ReaderObj *self)
{
    Py_XDECREF(self->fields);
    self->fields = PyList_New(0);
    if (self->fields == NULL)
        return -1;
    self->field_len = 0;
    self->state = START_RECORD;
    self->numeric_field = 0;
    return 0;
}

static PyObject *
Reader_iternext(ReaderObj *self)
{
    PyObject *lineobj;
    PyObject *fields = NULL;
    char *line, c;
    int linelen;

    if (parse_reset(self) < 0)
        return NULL;
    do {
        lineobj = PyIter_Next(self->input_iter);
        if (lineobj == NULL) {
            /* End of input OR exception */
            if (!PyErr_Occurred() && (self->field_len != 0 ||
                                      self->state == IN_QUOTED_FIELD)) {
                if (self->dialect->strict)
                    PyErr_SetString(error_obj, "unexpected end of data");
                else if (parse_save_field(self) >= 0 )
                    break;
            }
            return NULL;
        }
        ++self->line_num;

        line = PyString_AsString(lineobj);
        linelen = PyString_Size(lineobj);

        if (line == NULL || linelen < 0) {
            Py_DECREF(lineobj);
            return NULL;
        }
        while (linelen--) {
            c = *line++;
            if (c == '\0') {
                Py_DECREF(lineobj);
                PyErr_Format(error_obj,
                             "line contains NULL byte");
                goto err;
            }
            if (parse_process_char(self, c) < 0) {
                Py_DECREF(lineobj);
                goto err;
            }
        }
        Py_DECREF(lineobj);
        if (parse_process_char(self, 0) < 0)
            goto err;
    } while (self->state != START_RECORD);

    fields = self->fields;
    self->fields = NULL;
err:
    return fields;
}

static void
Reader_dealloc(ReaderObj *self)
{
    PyObject_GC_UnTrack(self);
    Py_XDECREF(self->pyfile);
    PyFile_DecUseCount(self->pyfile);
    Py_XDECREF(self->fields);
    if (self->field != NULL)
        PyMem_Free(self->field);

    PyObject_GC_Del(self);
}

static int
Reader_traverse(ReaderObj *self, visitproc visit, void *arg)
{
    Py_VISIT(self->pyfile);
    Py_VISIT(self->fields);
    return 0;
}

static int
Reader_clear(ReaderObj *self)
{
    Py_CLEAR(self->pyfile);
    Py_CLEAR(self->fields);
    return 0;
}

PyDoc_STRVAR(Reader_Type_doc,
"CSV reader\n"
"\n"
"Reader objects are responsible for reading and parsing tabular data\n"
"in CSV format.\n"
);

static struct PyMethodDef Reader_methods[] = {
    { NULL, NULL }
};
#define R_OFF(x) offsetof(ReaderObj, x)

static struct PyMemberDef Reader_memberlist[] = {
    { "line_num", T_ULONG, R_OFF(line_num), RO },
    { NULL }
};


static PyTypeObject Reader_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_csv.reader",                          /*tp_name*/
    sizeof(ReaderObj),                      /*tp_basicsize*/
    0,                                      /*tp_itemsize*/
    /* methods */
    (destructor)Reader_dealloc,             /*tp_dealloc*/
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
    Reader_Type_doc,                        /*tp_doc*/
    (traverseproc)Reader_traverse,          /*tp_traverse*/
    (inquiry)Reader_clear,                  /*tp_clear*/
    0,                                      /*tp_richcompare*/
    0,                                      /*tp_weaklistoffset*/
    PyObject_SelfIter,                          /*tp_iter*/
    (getiterfunc)Reader_iternext,           /*tp_iternext*/
    Reader_methods,                         /*tp_methods*/
    Reader_memberlist,                      /*tp_members*/
    0,                                      /*tp_getset*/

};

static PyObject *
csv_reader(PyObject *module, PyObject *args, PyObject *keyword_args)
{
    PyObject * iterator, * dialect = NULL;
    ReaderObj * self = PyObject_GC_New(ReaderObj, &Reader_Type);

    if (!self)
        return NULL;

    self->dialect = NULL;
    self->fields = NULL;
    self->input_iter = NULL;
    self->field = NULL;
    self->field_size = 0;
    self->line_num = 0;

    if (parse_reset(self) < 0) {
        Py_DECREF(self);
        return NULL;
    }

    if (!PyArg_UnpackTuple(args, "", 1, 2, &iterator, &dialect)) {
        Py_DECREF(self);
        return NULL;
    }
    self->input_iter = PyObject_GetIter(iterator);
    if (self->input_iter == NULL) {
        PyErr_SetString(PyExc_TypeError,
                        "argument 1 must be an iterator");
        Py_DECREF(self);
        return NULL;
    }
    self->dialect = (DialectObj *)_call_dialect(dialect, keyword_args);
    if (self->dialect == NULL) {
        Py_DECREF(self);
        return NULL;
    }

    PyObject_GC_Track(self);
    return (PyObject *)self;
}

/*
 * MODULE
 */

PyDoc_STRVAR(csv_module_doc,
"CSV parsing and writing.\n"
"\n"
"This module provides classes that assist in the reading and writing\n"
"of Comma Separated Value (CSV) files, and implements the interface\n"
"described by PEP 305.  Although many CSV files are simple to parse,\n"
"the format is not formally defined by a stable specification and\n"
"is subtle enough that parsing lines of a CSV file with something\n"
"like line.split(\",\") is bound to fail.  The module supports three\n"
"basic APIs: reading, writing, and registration of dialects.\n"
"\n"
"\n"
"DIALECT REGISTRATION:\n"
"\n"
"Readers and writers support a dialect argument, which is a convenient\n"
"handle on a group of settings.  When the dialect argument is a string,\n"
"it identifies one of the dialects previously registered with the module.\n"
"If it is a class or instance, the attributes of the argument are used as\n"
"the settings for the reader or writer:\n"
"\n"
"    class excel:\n"
"        delimiter = ','\n"
"        quotechar = '\"'\n"
"        escapechar = None\n"
"        doublequote = True\n"
"        skipinitialspace = False\n"
"        lineterminator = '\\r\\n'\n"
"        quoting = QUOTE_MINIMAL\n"
"\n"
"SETTINGS:\n"
"\n"
"    * quotechar - specifies a one-character string to use as the \n"
"        quoting character.  It defaults to '\"'.\n"
"    * delimiter - specifies a one-character string to use as the \n"
"        field separator.  It defaults to ','.\n"
"    * skipinitialspace - specifies how to interpret whitespace which\n"
"        immediately follows a delimiter.  It defaults to False, which\n"
"        means that whitespace immediately following a delimiter is part\n"
"        of the following field.\n"
"    * lineterminator -  specifies the character sequence which should \n"
"        terminate rows.\n"
"    * quoting - controls when quotes should be generated by the writer.\n"
"        It can take on any of the following module constants:\n"
"\n"
"        csv.QUOTE_MINIMAL means only when required, for example, when a\n"
"            field contains either the quotechar or the delimiter\n"
"        csv.QUOTE_ALL means that quotes are always placed around fields.\n"
"        csv.QUOTE_NONNUMERIC means that quotes are always placed around\n"
"            fields which do not parse as integers or floating point\n"
"            numbers.\n"
"        csv.QUOTE_NONE means that quotes are never placed around fields.\n"
"    * escapechar - specifies a one-character string used to escape \n"
"        the delimiter when quoting is set to QUOTE_NONE.\n"
"    * doublequote - controls the handling of quotes inside fields.  When\n"
"        True, two consecutive quotes are interpreted as one during read,\n"
"        and when writing, each quote character embedded in the data is\n"
"        written as two quotes\n");

PyDoc_STRVAR(csv_reader_doc,
"    csv_reader = reader(iterable [, dialect='excel']\n"
"                        [optional keyword args])\n"
"    for row in csv_reader:\n"
"        process(row)\n"
"\n"
"The \"iterable\" argument can be any object that returns a line\n"
"of input for each iteration, such as a file object or a list.  The\n"
"optional \"dialect\" parameter is discussed below.  The function\n"
"also accepts optional keyword arguments which override settings\n"
"provided by the dialect.\n"
"\n"
"The returned object is an iterator.  Each iteration returns a row\n"
"of the CSV file (which can span multiple input lines):\n");

PyDoc_STRVAR(csv_list_dialects_doc,
"Return a list of all know dialect names.\n"
"    names = csv.list_dialects()");

PyDoc_STRVAR(csv_get_dialect_doc,
"Return the dialect instance associated with name.\n"
"    dialect = csv.get_dialect(name)");

PyDoc_STRVAR(csv_register_dialect_doc,
"Create a mapping from a string name to a dialect class.\n"
"    dialect = csv.register_dialect(name, dialect)");

PyDoc_STRVAR(csv_unregister_dialect_doc,
"Delete the name/dialect mapping associated with a string name.\n"
"    csv.unregister_dialect(name)");

PyDoc_STRVAR(csv_field_size_limit_doc,
"Sets an upper limit on parsed fields.\n"
"    csv.field_size_limit([limit])\n"
"\n"
"Returns old limit. If limit is not given, no new limit is set and\n"
"the old limit is returned");

static struct PyMethodDef csv_methods[] = {
    { "reader", (PyCFunction)csv_reader,
        METH_VARARGS | METH_KEYWORDS, csv_reader_doc},
    { "list_dialects", (PyCFunction)csv_list_dialects,
        METH_NOARGS, csv_list_dialects_doc},
    { "register_dialect", (PyCFunction)csv_register_dialect,
        METH_VARARGS | METH_KEYWORDS, csv_register_dialect_doc},
    { "unregister_dialect", (PyCFunction)csv_unregister_dialect,
        METH_O, csv_unregister_dialect_doc},
    { "get_dialect", (PyCFunction)csv_get_dialect,
        METH_O, csv_get_dialect_doc},
    { "field_size_limit", (PyCFunction)csv_field_size_limit,
        METH_VARARGS, csv_field_size_limit_doc},
    { NULL, NULL }
};

PyMODINIT_FUNC
init_csv(void)
{
    PyObject *module;
    StyleDesc *style;

    if (PyType_Ready(&Dialect_Type) < 0)
        return;

    if (PyType_Ready(&Reader_Type) < 0)
        return;

    /* Create the module and add the functions */
    module = Py_InitModule3("_csv", csv_methods, csv_module_doc);
    if (module == NULL)
        return;

    /* Add version to the module. */
    if (PyModule_AddStringConstant(module, "__version__",
                                   MODULE_VERSION) == -1)
        return;

    /* Add _dialects dictionary */
    dialects = PyDict_New();
    if (dialects == NULL)
        return;
    if (PyModule_AddObject(module, "_dialects", dialects))
        return;

    /* Add quote styles into dictionary */
    for (style = quote_styles; style->name; style++) {
        if (PyModule_AddIntConstant(module, style->name,
                                    style->style) == -1)
            return;
    }

    /* Add the Dialect type */
    Py_INCREF(&Dialect_Type);
    if (PyModule_AddObject(module, "Dialect", (PyObject *)&Dialect_Type))
        return;

    /* Add the CSV exception object to the module. */
    error_obj = PyErr_NewException("_csv.Error", NULL, NULL);
    if (error_obj == NULL)
        return;
    PyModule_AddObject(module, "Error", error_obj);
}
