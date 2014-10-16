#include <Python.h>
#include "colmap.h"

int
ColMap_dealloc(ColMap *self)
{
    Py_DECREF(self->map);
    PyMem_Free(self);
    return 1;
}

ColMap*
ColMap_new(PyObject *map)
{
    if(!PyMapping_Check(map)){
        return NULL;
    }
    Py_INCREF(map);
    ColMap *self = PyMem_Malloc(sizeof(ColMap));
    if(self==NULL)
        return NULL;

    self->map = map;
    return self;
}

int
ColMap_get(ColMap* self, char *colname)
{
    PyObject* val = NULL;
    if(!PyMapping_HasKeyString(self->map, colname)){
        return -1;
    }
    val = PyMapping_GetItemString(self->map, colname);
    if(val==NULL)
        return -1;

    return (int)PyInt_AsLong(val);
}
