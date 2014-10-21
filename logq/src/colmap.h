#ifndef COLMAP_H
#define COLMAP_H

typedef struct {
    PyObject *map;
    int is_int;
    int lmap_len;
    int *lmap;
} ColMap;

int ColMap_dealloc(ColMap *self);

ColMap* ColMap_new(PyObject *map);

int ColMap_get(ColMap* self, char *colname);

int ColMap_get_int(ColMap* self, int colnum);

#endif
