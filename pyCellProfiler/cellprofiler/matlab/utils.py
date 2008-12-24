"""Utils.py - utility functions for manipulating the Matlab blackboard
    $Revision$
"""
import numpy
import tempfile
import scipy.io.matlab.mio
import os

def new_string_cell_array(shape):
    """Return a numpy.ndarray that looks like {NxM cell} to Matlab
    
    Return a numpy.ndarray that looks like {NxM cell} to Matlab.
    Each of the cells looks empty.
    shape - the shape of the array that's generated, e.g. (5,19) for a 5x19 cell array.
            Currently, this must be a 2-d shape.
    The object returned is a numpy.ndarray with dtype=dtype('object') and the given shape
    with each cell in the array filled with a numpy.ndarray with shape = (1,0) 
    and dtype=dtype('float64'). This appears to be the form that's created in matlab
    for this sort of object. 
    """
    result = numpy.ndarray(shape,dtype=numpy.dtype('object'))
    for i in range(0,shape[0]):
        for j in range(0,shape[1]):
            result[i,j] = numpy.empty((0,0)) 
    return result

def make_cell_struct_dtype(fields):
    """Makes the dtype of a struct composed of cells
    
    fields - the names of the fields in the struct
    """
    return numpy.dtype([(x,'|O4') for x in fields])

def get_int_from_matlab(proxy):
    """Given a proxy to an integer in Matlab, return the integer
    """
    return int(get_matlab_instance().num2str(proxy))

def load_into_matlab(handles):
    """Return a proxy object which is the data structure passed, loaded into Matlab
    """
    (matfd,matpath) = tempfile.mkstemp('.mat')
    matfh = os.fdopen(matfd,'wb')
    closed = False
    try:
        scipy.io.matlab.mio.savemat(matfh,handles,format='5',long_field_names=True)
        matfh.close()
        closed = True
        matlab = get_matlab_instance()
        return matlab.load(matpath)
    finally:
        if not closed:
            matfh.close()
        os.unlink(matpath)

def encapsulate_strings_in_arrays(handles):
    """Recursively descend through the handles structure, replacing strings as arrays packed with strings
    
    This function makes the handles structure loaded through the sandwich compatible with loadmat. It operates on the array in-place.
    """
    if handles.dtype.kind == 'O':
        # cells - descend recursively
        flat = handles.flat
        for i in range(0,len(flat)):
            if isinstance(flat[i],str) or isinstance(flat[i],unicode):
                flat[i] = encapsulate_string(flat[i])
            elif isinstance(flat[i],numpy.ndarray):
                encapsulate_strings_in_arrays(flat[i])
    elif handles.dtype.fields:
        # A structure: iterate over all structure elements.
        for field in handles.dtype.fields.keys():
            if isinstance(handles[field],str) or isinstance(handles[field],unicode):
                handles[field] = encapsulate_string(handles[field])
            elif isinstance(handles[field],numpy.ndarray):
                encapsulate_strings_in_arrays(handles[field])

def encapsulate_string(s):
    """Encapsulate a string in an array of shape 1 of the length of the string
    """
    if isinstance(s,str):
        result = numpy.ndarray((1,),'<S%d'%(len(s)))
    else:
        result = numpy.ndarray((1,),'<U%d'%(len(s)))
    result[0]=s
    return result;

def get_matlab_instance():
    global __MATLAB
    if not globals().has_key('__MATLAB'):
        import mlabwrap
        __MATLAB = mlabwrap.mlab
        try:
            __MATLAB.desktop()
        except:
            pass
    return __MATLAB

def g_cell_fun():
    return get_matlab_instance().eval('@(cell,x) cell{x+1}')

def s_cell_fun():
    return get_matlab_instance().eval('@(cell,x,value) {cell{1:x},value,cell{x+2:end}}')
