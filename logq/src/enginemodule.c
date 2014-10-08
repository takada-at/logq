#define MODULE_VERSION "0.0.1"

#include <Python.h>
#include <structmember.h>

typedef struct {
    char *op;
    char *arg;
} Expr;

typedef struct {
    PyObject_HEAD

    int start;
    int success;
    int fail;
    int state;
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
    for(i=0; i<self->exprsize; ++i){
        tmp = self->exprs + i;
        free(tmp->op);
        free(tmp->arg);
        free(self->exprs + i);
    }
    free(self->exprs);
    free(self->expr_table);
    free(self->success_table);
    free(self->fail_table);
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

static Expr *
construct_expr(PyObject *pyexpr)
{
    int opsize, argsize;
    char *py_op;
    char *py_arg;
    char *op;
    char *arg;
    Expr *expr;
    if(!PyArg_ParseTuple(pyexpr, "ss", &py_op, &py_arg))
        return NULL;

    opsize  = strlen(py_op) + 1;
    argsize = strlen(py_arg) + 1;
    op   = malloc(sizeof(char) * opsize);
    arg  = malloc(sizeof(char) * argsize);
    expr = malloc(sizeof(expr));
    if(op==NULL || arg==NULL || expr)
        return NULL;

    strcpy(op, py_op);
    strcpy(arg, py_arg);
    expr->op = op;
    expr->arg = arg;
    return expr;
}

static PyObject *
Engine_init(Engine *self, PyObject *args, PyObject *kwargs)
{
    int start;
    int success;
    int fail;
    int colsize;
    int statesize;
    int exprsize;
    int i, j;
    int val;
    PyObject *py_exprs = NULL;
    PyObject *py_expr_table = NULL;
    PyObject *py_success_table = NULL;
    PyObject *py_fail_table = NULL;
    PyObject *py_expr = NULL;
    Expr *expr = NULL;
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
        return NULL;

    colsize          = PyList_Size(PyList_GetItem(py_expr_table, 0));
    statesize        = PyList_Size(py_expr_table);
    exprsize         = PyList_Size(py_exprs);
    exprs         = malloc( sizeof(Expr) * exprsize );
    expr_table    = malloc( sizeof(int) * statesize * colsize);
    success_table = malloc( sizeof(int) * statesize * colsize);
    fail_table    = malloc( sizeof(int) * statesize * colsize);
    if(exprs == NULL || expr_table == NULL || success_table == NULL
       || fail_table == NULL)
        return PyErr_NoMemory();

    for(i=0; i<exprsize; ++i){
        py_expr = PyList_GetItem(PyList_GetItem(py_expr_table, i), j);
        expr = construct_expr(py_expr);
        if(expr==NULL)
            return NULL;
        exprs[i] = *expr;
    }
    for(i=0; i<statesize; ++i){
        for(j=0; j<colsize; ++j){
            if(!PyArg_Parse(PyList_GetItem(PyList_GetItem(py_expr_table, i), j), "i", &val))
                return NULL;
            expr_table[i*colsize + j]    = val;
            if(!PyArg_Parse(PyList_GetItem(PyList_GetItem(py_success_table, i), j), "i", &val))
                return NULL;
            success_table[i*colsize + j] = val;
            if(!PyArg_Parse(PyList_GetItem(PyList_GetItem(py_fail_table, i), j), "i", &val))
                return NULL;
            fail_table[i*colsize + j]    = val;
        }
    }
    self->start     = start;
    self->state     = start;
    self->success   = success;
    self->fail      = fail;
    self->colsize   = colsize;
    self->statesize = statesize;
    self->exprsize  = exprsize;
    self->expr_table    = expr_table;
    self->success_table = success_table;
    self->fail_table    = fail_table;
    self->exprs         = exprs;
    return (PyObject *)self;
}

static PyMemberDef Engine_members[] = {
    {"state",   T_INT, offsetof(Engine, state), READONLY },
    {"start",   T_INT, offsetof(Engine, start), READONLY },
    {"success", T_INT, offsetof(Engine, success), READONLY },
    {"fail",    T_INT, offsetof(Engine, fail), READONLY },
    {NULL}
};

static struct PyMethodDef Engine_methods[] = {
    {NULL}
};

static PyTypeObject EngineType = {
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
    { NULL}
};

#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initengine(void)
{
    PyObject *module;
    if (PyType_Ready(&EngineType) < 0)
        return;

    module = Py_InitModule3("engine", engine_methods, engine_module_doc);
    if (module == NULL)
        return;

    if (PyModule_AddStringConstant(module, "__version__",
                                   MODULE_VERSION) == -1)
        return;

    Py_INCREF(&EngineType);
    if (PyModule_AddObject(module, "Engine", (PyObject *)&EngineType))
        return;
}
