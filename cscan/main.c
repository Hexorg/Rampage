#include <Python.h>
static PyObject *ScanError;

#define unlikely(x)    __builtin_expect(!!(x), 0) 

PyObject *matchbufferToDict(int *matchbuffer, int size, Py_ssize_t typeCount, PyObject *allKeys[]) {
    PyObject *result = PyDict_New();
    for (Py_ssize_t i=0; i<size; i++) {
        PyObject *match_set = PySet_New(NULL);
        for (Py_ssize_t T=0; T<typeCount; T++) {
            if (matchbuffer[i*(typeCount+1)+T]) {
                PySet_Add(match_set, allKeys[T]);
            }
        }
        PyDict_SetItem(result, PyLong_FromLong(matchbuffer[i*(typeCount+1)+typeCount]), match_set);
    }
    return result;
}

PyObject *scan(const char *buffer, int BUFFLEN, PyObject *dict) {
    // expecting values of dict to only ever be PyBytes
    Py_ssize_t ppos, T;
    PyObject *pkey,*pvalue;
    const Py_ssize_t typeCount = PyDict_Size(dict);
    int isMatches[typeCount];
    PyObject *allKeys[typeCount];
    int isMatched;
    int *matchbuffer = malloc(BUFFLEN * (typeCount+1)) ;
    int matchbufferpos = 0;

    ppos = 0;
    T = 0;
    while(PyDict_Next(dict, &ppos, &pkey, &pvalue)) {
        allKeys[T++] = pkey;
    }
    for (int offset=0; offset<BUFFLEN; offset++) {
        isMatched = 0;
        T = 0;
        ppos = 0;
        while(PyDict_Next(dict, &ppos, &pkey, &pvalue)) {
            const char *value = PyBytes_AsString(pvalue);
            switch(PyBytes_Size(pvalue)) {
                case 1: isMatches[T] = *(buffer+offset) == *value; break;
                case 2: isMatches[T] = *((short* ) (buffer+offset)) == *(short *) value; break;
                case 4: isMatches[T] = *((int* ) (buffer+offset)) == *(int *) value; break;
                case 8: isMatches[T] = *((long* ) (buffer+offset)) == *(long *) value; break;
                default: PyErr_SetString(ScanError, "Dictionary values must be 1, 2, 4, or 8 bytes long"); return NULL;
            }
            isMatched |= isMatches[T];
            T++;
        }
        if (unlikely(isMatched)) {
            for (Py_ssize_t i=0; i<typeCount; i++) {
                matchbuffer[matchbufferpos*(typeCount+1) + i] = isMatches[i];
            }
            matchbuffer[matchbufferpos*(typeCount+1)+typeCount] = offset;
            matchbufferpos++;
        }
    }
    PyObject *result = matchbufferToDict(matchbuffer, matchbufferpos, typeCount, allKeys);
    free(matchbuffer);
    return result;
}

static PyObject *start_scan(PyObject *self, PyObject *args) {
    const char *buffer; // s#
    int buffer_length;
    PyObject *type_value_dict; // O!
    if (!PyArg_ParseTuple(args, "s#O!", &buffer, &buffer_length, &PyDict_Type, &type_value_dict)) {
        return NULL;
    }
    Py_ssize_t ppos = 0;
    PyObject *pkey,*pvalue;
    while (PyDict_Next(type_value_dict, &ppos, &pkey, &pvalue)) {
        if (!PyBytes_Check(pvalue)) {
            PyErr_SetString(ScanError, "One or more items of the dictionary is not a byte object");
            return NULL;
        }
    }
    return scan(buffer, buffer_length, type_value_dict);
}

PyObject *filter(const char *buffer, int BUFFLEN, PyObject *typeValues, PyObject *matches) {
    Py_ssize_t pmatchpos, ptypepos, offset, T;
    PyObject *poffset, *pmatchtypeset, *ptype, *pvalue;
    const Py_ssize_t typeCount = PyDict_Size(typeValues);
    int isMatches[typeCount];
    int isMatched;
    PyObject *allKeys[typeCount];
    int *matchbuffer = malloc(PyDict_Size(matches) * (typeCount+1)) ;
    int matchbufferpos = 0;

    ptypepos = 0;
    T = 0;
    while(PyDict_Next(typeValues, &ptypepos, &ptype, &pvalue)) {
        allKeys[T++] = ptype;
    }
    pmatchpos = 0;
    while(PyDict_Next(matches, &pmatchpos, &poffset, &pmatchtypeset)) {
        offset = PyLong_AsLong(poffset);
        isMatched = 0;
        T = 0;
        ptypepos = 0;
        while(PyDict_Next(typeValues, &ptypepos, &ptype, &pvalue)) {
            if (PySet_Contains(pmatchtypeset, ptype)) {
                const char *value = PyBytes_AsString(pvalue);
                switch(PyBytes_Size(pvalue)) {
                    case 1: isMatches[T] = *(buffer+offset) == *value; break;
                    case 2: isMatches[T] = *((short* ) (buffer+offset)) == *(short *) value; break;
                    case 4: isMatches[T] = *((int* ) (buffer+offset)) == *(int *) value; break;
                    case 8: isMatches[T] = *((long* ) (buffer+offset)) == *(long *) value; break;
                    default: PyErr_SetString(ScanError, "Dictionary values must be 1, 2, 4, or 8 bytes long"); return NULL;
                }
                isMatched |= isMatches[T];
                T++;
            }
        }
        if (unlikely(isMatched)) {
            for (Py_ssize_t i=0; i<typeCount; i++) {
                matchbuffer[matchbufferpos*(typeCount+1) + i] = isMatches[i];
            }
            matchbuffer[matchbufferpos*(typeCount+1)+typeCount] = offset;
            matchbufferpos++;
        }
    }
    PyObject *result = matchbufferToDict(matchbuffer, matchbufferpos, typeCount, allKeys);
    free(matchbuffer);
    return result;
}

static PyObject *start_filter(PyObject *self, PyObject *args) {
    const char *buffer; // s#
    int buffer_length;
    PyObject *type_value_dict; // O!
    PyObject *old_matches_dict; // O!
    if (!PyArg_ParseTuple(args, "s#O!O!", &buffer, &buffer_length, &PyDict_Type, &type_value_dict, &PyDict_Type, &old_matches_dict)) {
        return NULL;
    }
    Py_ssize_t ppos = 0;
    PyObject *pkey,*pvalue;
    while (PyDict_Next(type_value_dict, &ppos, &pkey, &pvalue)) {
        if (!PyBytes_Check(pvalue)) {
            PyErr_SetString(ScanError, "One or more items of the dictionary is not a byte object");
            return NULL;
        }
    }
    ppos = 0;
    while (PyDict_Next(old_matches_dict, &ppos, &pkey, &pvalue)) {
        if (!PyLong_Check(pkey)) {
            PyErr_SetString(ScanError, "One or more keys of the dictionary is not an integer");
            return NULL;
        }
        if (!PySet_Check(pvalue)) {
            PyErr_SetString(ScanError, "One or more items of the dictionary is not a set object");
            return NULL;
        }
    }
    return filter(buffer, buffer_length, type_value_dict, old_matches_dict);
}

static PyMethodDef MethodTable[] = {
    {"scan", start_scan, METH_VARARGS, "Scan the buffer for provided values"},
    {"filter", start_filter, METH_VARARGS, "Filter previous scan results"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef scanmodule = {
    PyModuleDef_HEAD_INIT,
    "cscan",
    NULL, // module documentation
    -1, // size of per-interpreter state of the module
    MethodTable
};

PyMODINIT_FUNC PyInit_cscan(void) {
    PyObject *module = PyModule_Create(&scanmodule);
    if (module == NULL) {
        return module;
    }

    ScanError = PyErr_NewException("cscan.error", NULL, NULL);
    Py_INCREF(ScanError);
    PyModule_AddObject(module, "error", ScanError);
    return module;
}