#define MODULE_VERSION "0.0.1"

#define STR_EQ 1

#include <Python.h>
#include <structmember.h>

#include "engine.h"
#include "csv.h"

/**
 * Engine
 */
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
    if(col >= self->colsize)
        return 0;

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

PyTypeObject Engine_Type = {
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
