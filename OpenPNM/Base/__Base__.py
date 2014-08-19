"""
module __OpenPNMbase__: contains OpenPNM base classes
=====================================================

"""
import os, string, random, time, shutil
import OpenPNM
import scipy as sp
import scipy.constants
import logging as _logging


# set up logging to file - see previous section for more details
_logging.basicConfig(level=_logging.ERROR,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    )
                    
class Base(dict):
    r"""
    .. class:: `OpenPNM.Base` -- Base class for OpenPNM
    
    
    Base class with a few bells and whistles..
    
    Parameters
    ----------    
    
    loglevel : int
        Level of the logger (10=Debug, 20=INFO, 30=Warning, 40=Error, 50=Critical)
    loggername : string
        Name of the logger. The default is the name of the class.

    Attributes
    ----------
    
    self._logger : _logging.logger
       This class defines a logger for the class and all classes inheriting from it.
       it supports all settings of the standard logger. It still needs some fine 
       tuning.
           
       ======== =====   =============================================================
       Level    Value   When it is used
       ======== =====   =============================================================
       DEBUG    10      Detailed information, at diagnostic stage
       INFO     20      Confirmation that things are working as expected.
       WARNING  30      An indication that something unexpected happened.
       ERROR    40      Due to a more serious problem, program might still execute.
       CRITICAL 50      A serious error, might compromise program execution
       ======== =====   =============================================================
       
    """
    _name = None
    def __init__(self,**kwargs):
        super(Base,self).__init__()
        if 'loggername' in kwargs.keys():
            self._logger = _logging.getLogger(kwargs['loggername'])
        else:
            self._logger = _logging.getLogger(self.__class__.__name__)
        if 'loglevel' in kwargs.keys():
            loglevel = kwargs['loglevel']
            self.set_loglevel(loglevel)
        else:
            loglevel = 30
            self.set_loglevel(loglevel)
        
        #Initialize phase, physics, and geometry tracking lists
        self._phases = []
        self._geometries = []
        self._physics = []
        self._net = []
        
    def __repr__(self):
        return '<%s.%s object at %s>' % (
        self.__class__.__module__,
        self.__class__.__name__,
        hex(id(self)))
              
    def set_loglevel(self,level=50):
        r"""
        Sets the effective log level for this class
        
        Parameters
        ----------
        level : int
            Level above which messages should be logged.
        """
        self._logger.setLevel(level)
        self._logger.debug("Changed log level")
            
    def find_object(self,obj_name='',obj_type=''):
        r'''
        Find objects associated with a given network model by name or type
        
        Parameters
        ----------
        obj_name : string
           Name of sought object
           
        obj_type : string
            The type of object beign sought.  Options are:
            
            1. 'Network'
            2. 'Geometry'
            3. 'Phases'
            4. 'Physics'
        
        Returns
        -------
        OpenPNM object or list of objects
        
        Examples
        --------
        >>> pn = OpenPNM.Network.TestNet()
        >>> geom = OpenPNM.Geometry.Stick_and_Ball(network=pn,name='geo1')
        >>> temp = pn.find_object(obj_name='geo1')
        >>> temp.name
        'geo1'
        >>> temp = pn.find_object(obj_type='Geometry')
        >>> temp[0].name
        'geo1'
        
        '''
        if self.__module__.split('.')[1] == 'Network':
            net = self
        else:
            net = self._net
        
        if obj_name != '':
            objs = []
            if self.name == obj_name:
                return self
            if net.name == obj_name:
                return net
            for geom in net._geometries:
                if geom.name == obj_name:
                    return geom
            for phase in net._phases:
                if phase.name == obj_name:
                    return phase
            for phys in net._physics:
                if phys.name == obj_name:
                    return phys
            return objs # Return empty list if none found
        elif obj_type != '':
            objs = []
            for geom in net._geometries:
                if geom.__class__.__module__.split('.')[1] == obj_type:
                    objs.append(geom)
            for phys in net._physics:
                if phys.__class__.__module__.split('.')[1] == obj_type:
                    objs.append(phys)
            for phase in net._phases:
                if phase.__class__.__module__.split('.')[1] == obj_type:
                    objs.append(phase)
            return objs
            
    def physics(self,name=''):
        r'''
        Retrieves Physics assocaiated with the object
        
        Parameters
        ----------
        name : string, optional
            The name of the Physics object to retrieve
        Returns
        -------
            If name is NOT provided, then a list of Physics names is returned. 
            If a name IS provided, then the Physics object of that name is 
            returned.
        '''
        if name == '':
            phys = []
            for item in self._physics:
                phys.append(item.name)
        else:
            phys = self.find_object(obj_name=name)
        return phys
        
    def phases(self,name=''):
        r'''
        Retrieves Phases assocaiated with the object
        
        Parameters
        ----------
        name : string, optional
            The name of the Phase object to retrieve.  
        Returns
        -------
            If name is NOT provided, then a list of phase names is returned. If
            a name IS provided, then the Phase object of that name is returned.
        '''
        if name == '':
            phases = []
            for item in self._phases:
                phases.append(item.name)
        else:
            phases = self.find_object(obj_name=name)
        return phases
        
    def geometries(self,name=''):
        r'''
        Retrieves Geometry associated with the object
        
        Parameters
        ----------
        name : string, optional
            The name of the Geometry object to retrieve.  
        Returns
        -------
            If name is NOT provided, then a list of Geometry names is returned. 
            If a name IS provided, then the Geometry object of that name is 
            returned.
        '''
        if name == '':
            geoms = []
            for item in self._geometries:
                geoms.append(item.name)
        else:
            geoms = self.find_object(obj_name=name)
        return geoms
        
    def network(self,name=''):
        r'''
        Retrieves the network associated with the object.  If the object is
        a network, then it returns the parent network from which the present
        object derives, or return an empty list if it has not parents.
        
        Parameters
        ----------
        name : string, optional
            The name of the Geometry object to retrieve.  
            
        Returns
        -------
            If name is NOT provided, then the name of the parent is returned. 
            If a name IS provided, then the parent netowrk object is returned.
        '''
        if name == '':
            try:
                net = self._net.name
            except:
                net = []
        else:
            net = self._net
        return net
            
    def delete_object(self,obj=None,obj_name=''):
        r'''
        Remove specific objects from a model
        
        Parameters
        ----------
        name : string
            The name of the object to delete
            
        Examples
        --------
        >>> pn = OpenPNM.Network.TestNet()
        >>> geom = OpenPNM.Geometry.Stick_and_Ball(network=pn,name='geo')
        >>> geom.name
        'geo'
        >>> pn.delete_object(obj_name='geo')
        >>> pn.find_object(obj_name='geo')
        []
        
        '''
        if self.__class__.__module__.split('.')[1] == 'Network':
            net = self
        else:
            net = self._net
        if obj_name != '':
            obj = self.find_object(obj_name=obj_name)
        #Get object type, so we know where to delete from
        obj_type = obj.__class__.__module__.split('.')[1]
        if obj_type == 'Geometry':  # Remove geometry from network
            net._geometries.remove(obj)
            net.pop('pore.'+obj.name,None)
            net.pop('throat.'+obj.name,None)
        elif obj_type == 'Phases':
            for phase in net._phases:
                if phase == obj:
                    for physics in phase._physics:
                        physics._phase = None
                        net._physics.remove(physics)
                    net._phases.remove(obj)
                    del phase
        elif obj_type == 'Physics':
            for physics in net._physics:
                if physics == obj:
                    for phase in physics._phase:
                        phase._physics.remove(obj)
                        phase.pop('pore.'+obj.name,None)
                        phase.pop('throat.'+obj.name,None)
                    net._physcis.remove(obj)
                    del phase
                    
    def _set_name(self,name):
        if self._name != None:
            self._logger.error('Renaming objects can have catastrophic consequences')
            return
        if name == None:
            name = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(5))
            name = self.__module__.split('.')[-1].strip('__') + '_' + name
        if self.find_object(obj_name=name) != []:
            self._logger.error('An object with this name already exists')
            return
        self._name = name
    
    def _get_name(self):
        return self._name
        
    name = property(_get_name,_set_name)
            
    def save_object(self,filename):
        r'''
        Save the current object's data to a Numpy zip file.
        
        Parameters
        ----------
        filename : string
            File name (including path if desired) to save to
        '''
        temp = filename.split('.')[0]
        temp = temp+'.npz'
        sp.savez_compressed(temp,**self)
        
    def save_model(self):
        r'''
        Save the current simulation in it's entirity.  
        
        '''
        
        if self.__module__.split('.')[1] == 'Network':
            net = self
        else:
            net = self._net
        print('Make temporary directory to store numpy zip files')
        dirname = 'temp'
        try:
            os.mkdir(dirname)
        except:
            raise Exception('A model with that name already exists')
            
        #Save network
        print('Save numpy zip files for each object')
        sp.savez_compressed(dirname+'/'+'Network'+'.'+net.name+'.npz',**self)
        #Save other objects
        for geom in net._geometries:
            filename = dirname+'/'+'Geometry'+'.'+geom.name+'.npz'
            sp.savez_compressed(filename,**geom)
        for phase in net._phases:
            filename = dirname+'/'+'Phase'+'.'+phase.name+'.npz'
            sp.savez_compressed(filename,**phase)
            for phys in phase._physics:
                filename = dirname+'/'+'Physics'+'.'+phys.name+'.'+'Phase'+'.'+phase.name+'.npz'
                sp.savez_compressed(filename,**phys)
        
        #Convert 'temp' directory into a 'pnm' file and remove temp
        print('Generate a zip archive from the temporary directory')
        shutil.make_archive(base_name=net.name, format="zip", root_dir='temp')
        print('Remove temporary directory')
        shutil.rmtree('temp')
        print('Rename zip file to a pnm file')
        os.rename(net.name+'.zip',net.name+'.pnm')

if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)


























