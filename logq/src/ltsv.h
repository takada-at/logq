#ifndef LTSV_H
#define LTSV_H

#include "colmap.h"

typedef enum {
    START_RECORD, START_LABEL, IN_LABEL, 
    IN_FIELD, EAT_CRNL, QUERY_FAIL
} ParserState;

typedef struct {
    PyObject_HEAD

    Engine *engine;
    ColMap *colmap;
    char **valmap;
    PyObject *pyfile;
    FILE *file;
    PyObject *fields;           /* field list for current record */
    ParserState state;          /* current CSV parse state */
    char *field;                /* build current field in here */
    char *label;                /* build current field in here */
    int label_len;
    int field_size;             /* size of allocated buffer */
    int field_len;              /* length of current field */
    int val_len;
    int val_size;
    int col;
    int is_file;
    unsigned long line_num;     /* Source-file line number */
} LTSVParser;


int register_ltsv(PyObject *module);
#endif
