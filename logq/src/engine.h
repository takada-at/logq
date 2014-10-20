#ifndef ENGINE_H
#define ENGINE_H

extern PyTypeObject Engine_Type;

typedef enum {
    NOP, STR_EQ, STR_NE, STR_LT, STR_LE, STR_GT, STR_GE, STR_IN, STR_NIN,
    TOP, BTM
} Operator;

typedef struct {
    Operator op;
    char *arg;
} Expr;

typedef struct {
    PyObject_HEAD

    int start;
    int success;
    int fail;
    int state;
    int is_success;
    int is_file;
    int is_fail;
    int colsize;
    int statesize;
    int exprsize;
    int *expr_table;
    int *success_table;
    int *fail_table;
    Expr *exprs;
} Engine;

int Engine_read(Engine *self, int col, const char* val);

PyObject* Engine_reset(Engine *self);

int register_engine(PyObject *module);

#endif
