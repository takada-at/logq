#include "gtest/gtest.h"

#include <Python.h>
extern "C"
{
#include "engine.h"
}

TEST(AddTest, Test1)
{
ASSERT_EQ(2, 1+1);
}

TEST(EngineTest, Test1)
{
    PyObject *pName, *pModule, *pDict, *pFunc;
    PyObject *pArgs, *pValue;
    Py_Initialize();
    pName = PyString_FromString("engine");
    pModule = PyImport_Import(pName);
    Py_DECREF(pName);
    pFunc = PyObject_GetAttrString(pModule, argv[2]);
}

int main(int argc, char **argv) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
