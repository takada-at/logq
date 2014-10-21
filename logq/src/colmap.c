#include <Python.h>
#include "colmap.h"

int
ColMap_dealloc(ColMap *self)
{
    Py_DECREF(self->map);
    if(self->lmap!=NULL)
        PyMem_Free(self->lmap);
    PyMem_Free(self);
    return 1;
}

int
ColMap_construct_list(ColMap *self, PyObject *map)
{
    int i = 0, len = 0;
    int *lmap;
    PyObject*tmp;
    if(!PySequence_Check(map)){
        return 0;
    }
    len = (int)PySequence_Size(map);
    if(len<0)
        return 0;

    self->lmap_len = len;
    lmap = PyMem_Malloc(sizeof(int) * len);
    if(lmap==NULL)
        return 0;
    for(i=0; i<len; ++i){
        tmp = PySequence_ITEM(map, (Py_ssize_t)i);
        if(tmp==NULL){
            return 0;
        }
        lmap[i] = (int)PyInt_AsLong(tmp);
    }
    self->lmap = lmap;
    return 1;
}
ColMap*
ColMap_new(PyObject *map)
{
    ColMap *self = PyMem_Malloc(sizeof(ColMap));
    self->lmap = NULL;
    if(self==NULL){
        return NULL;
    }
    if(!PyMapping_Check(map)){
        if(!ColMap_construct_list(self, map))
            return NULL;
        self->is_int = 1;
    }else{
        self->is_int = 0;
    }
    Py_INCREF(map);
    self->map = map;
    return self;
}

int
ColMap_get_int(ColMap* self, int colnum)
{
    if(colnum < self->lmap_len)
        return self->lmap[colnum];

    return -1;
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
