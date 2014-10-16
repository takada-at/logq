#ifndef COLMAP_H
#define COLMAP_H

typedef struct {
    PyObject *map;
} ColMap;

int ColMap_dealloc(ColMap *self);

ColMap* ColMap_new(PyObject *map);

int ColMap_get(ColMap* self, char *colname);

#endif
