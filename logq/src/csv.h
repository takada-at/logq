#ifndef CSV_H
#define CSV_H

typedef enum {
    START_RECORD, START_FIELD, IN_FIELD,
    IN_QUOTED_FIELD, QUOTE_IN_QUOTED_FIELD,
    EAT_CRNL, QUERY_FAIL, QUERY_FAIL_EAT_CRNL
} ParserState;

typedef struct {
    PyObject_HEAD

    Engine *engine;
    PyFileObject *pyfile;
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


int register_csv(PyObject *module);
#endif
