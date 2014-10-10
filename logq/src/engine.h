#ifndef ENGINE_H
#define ENGINE_H

extern PyTypeObject Engine_Type;

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

int Engine_read(Engine *self, int col, const char* val);

PyObject * Engine_reset(Engine *self);
#endif
