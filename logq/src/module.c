#define MODULE_VERSION "0.0.1"

#include <Python.h>

#include "engine.h"
#include "csv.h"
#include "ltsv.h"

PyDoc_STRVAR(engine_module_doc,
             "");

static PyMethodDef engine_methods[] = {
    { NULL }
};


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
    register_ltsv(module);
}
