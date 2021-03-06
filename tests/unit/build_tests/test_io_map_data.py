from hdmf.spec import AttributeSpec, DatasetSpec, DtypeSpec, SpecCatalog, SpecNamespace, NamespaceCatalog
from hdmf.build import DatasetBuilder, ObjectMapper, BuildManager, TypeMap
from hdmf import Data
from hdmf.utils import docval, getargs, call_docval_func
from hdmf.testing import TestCase

import h5py
import numpy as np
import os

from tests.unit.utils import CORE_NAMESPACE


class Baz(Data):

    @docval({'name': 'name', 'type': str, 'doc': 'the name of this Baz'},
            {'name': 'data', 'type': (list, h5py.Dataset), 'doc': 'some data'},
            {'name': 'baz_attr', 'type': str, 'doc': 'an attribute'})
    def __init__(self, **kwargs):
        name, data, baz_attr = getargs('name', 'data', 'baz_attr', kwargs)
        super().__init__(name=name, data=data)
        self.__baz_attr = baz_attr

    @property
    def baz_attr(self):
        return self.__baz_attr


class TestDataMap(TestCase):

    def setUp(self):
        self.setUpBazSpec()
        self.spec_catalog = SpecCatalog()
        self.spec_catalog.register_spec(self.baz_spec, 'test.yaml')
        self.namespace = SpecNamespace('a test namespace', CORE_NAMESPACE, [{'source': 'test.yaml'}],
                                       version='0.1.0',
                                       catalog=self.spec_catalog)
        self.namespace_catalog = NamespaceCatalog()
        self.namespace_catalog.add_namespace(CORE_NAMESPACE, self.namespace)
        self.type_map = TypeMap(self.namespace_catalog)
        self.type_map.register_container_type(CORE_NAMESPACE, 'Baz', Baz)
        self.type_map.register_map(Baz, ObjectMapper)
        self.manager = BuildManager(self.type_map)
        self.mapper = ObjectMapper(self.baz_spec)

    def setUpBazSpec(self):
        self.baz_spec = DatasetSpec('an Baz type', 'int', name='MyBaz', data_type_def='Baz', shape=[None],
                                    attributes=[AttributeSpec('baz_attr', 'an example string attribute', 'text')])

    def test_build(self):
        ''' Test default mapping functionality when no attributes are nested '''
        container = Baz('my_baz', list(range(10)), 'abcdefghijklmnopqrstuvwxyz')
        builder = self.mapper.build(container, self.manager)
        expected = DatasetBuilder('my_baz', list(range(10)), attributes={'baz_attr': 'abcdefghijklmnopqrstuvwxyz'})
        self.assertDictEqual(builder, expected)

    def test_append(self):
        with h5py.File('test.h5', 'w') as file:
            test_ds = file.create_dataset('test_ds', data=[1, 2, 3], chunks=True, maxshape=(None,))
            container = Baz('my_baz', test_ds, 'abcdefghijklmnopqrstuvwxyz')
            container.append(4)
            np.testing.assert_array_equal(container[:], [1, 2, 3, 4])
        os.remove('test.h5')

    def test_extend(self):
        with h5py.File('test.h5', 'w') as file:
            test_ds = file.create_dataset('test_ds', data=[1, 2, 3], chunks=True, maxshape=(None,))
            container = Baz('my_baz', test_ds, 'abcdefghijklmnopqrstuvwxyz')
            container.extend([4, 5])
            np.testing.assert_array_equal(container[:], [1, 2, 3, 4, 5])
        os.remove('test.h5')


class BazScalar(Data):

    @docval({'name': 'name', 'type': str, 'doc': 'the name of this BazScalar'},
            {'name': 'data', 'type': int, 'doc': 'some data'})
    def __init__(self, **kwargs):
        call_docval_func(super().__init__, kwargs)


class TestDataMapScalar(TestCase):

    def setUp(self):
        self.setUpBazSpec()
        self.spec_catalog = SpecCatalog()
        self.spec_catalog.register_spec(self.baz_spec, 'test.yaml')
        self.namespace = SpecNamespace('a test namespace', CORE_NAMESPACE, [{'source': 'test.yaml'}],
                                       version='0.1.0',
                                       catalog=self.spec_catalog)
        self.namespace_catalog = NamespaceCatalog()
        self.namespace_catalog.add_namespace(CORE_NAMESPACE, self.namespace)
        self.type_map = TypeMap(self.namespace_catalog)
        self.type_map.register_container_type(CORE_NAMESPACE, 'BazScalar', BazScalar)
        self.type_map.register_map(BazScalar, ObjectMapper)
        self.manager = BuildManager(self.type_map)
        self.mapper = ObjectMapper(self.baz_spec)

    def setUpBazSpec(self):
        self.baz_spec = DatasetSpec('a BazScalar type', 'int', name='MyBaz', data_type_def='BazScalar')

    def test_construct_scalar_dataset(self):
        """Test constructing a Data object with an h5py.Dataset with shape (1, ) for scalar spec."""
        with h5py.File('test.h5', 'w') as file:
            test_ds = file.create_dataset('test_ds', data=[1])
            expected = BazScalar(
                name='my_baz',
                data=1,
            )
            builder = DatasetBuilder(
                name='my_baz',
                data=test_ds,
                attributes={'data_type': 'BazScalar',
                            'namespace': CORE_NAMESPACE,
                            'object_id': expected.object_id},
            )
            container = self.mapper.construct(builder, self.manager)
            self.assertTrue(np.issubdtype(type(container.data), np.integer))  # as opposed to h5py.Dataset
            self.assertContainerEqual(container, expected)
        os.remove('test.h5')


class BazScalarCompound(Data):

    @docval({'name': 'name', 'type': str, 'doc': 'the name of this BazScalar'},
            {'name': 'data', 'type': 'array_data', 'doc': 'some data'})
    def __init__(self, **kwargs):
        call_docval_func(super().__init__, kwargs)


class TestDataMapScalarCompound(TestCase):

    def setUp(self):
        self.setUpBazSpec()
        self.spec_catalog = SpecCatalog()
        self.spec_catalog.register_spec(self.baz_spec, 'test.yaml')
        self.namespace = SpecNamespace('a test namespace', CORE_NAMESPACE, [{'source': 'test.yaml'}],
                                       version='0.1.0',
                                       catalog=self.spec_catalog)
        self.namespace_catalog = NamespaceCatalog()
        self.namespace_catalog.add_namespace(CORE_NAMESPACE, self.namespace)
        self.type_map = TypeMap(self.namespace_catalog)
        self.type_map.register_container_type(CORE_NAMESPACE, 'BazScalarCompound', BazScalarCompound)
        self.type_map.register_map(BazScalarCompound, ObjectMapper)
        self.manager = BuildManager(self.type_map)
        self.mapper = ObjectMapper(self.baz_spec)

    def setUpBazSpec(self):
        self.baz_spec = DatasetSpec(
            doc='a BazScalarCompound type',
            dtype=[
                DtypeSpec(
                    name='id',
                    dtype='uint64',
                    doc='The unique identifier in this table.'
                ),
                DtypeSpec(
                    name='attr1',
                    dtype='text',
                    doc='A text attribute.'
                ),
            ],
            name='MyBaz',
            data_type_def='BazScalarCompound',
        )

    def test_construct_scalar_compound_dataset(self):
        """Test construct on a compound h5py.Dataset with shape (1, ) for scalar spec does not resolve the data."""
        with h5py.File('test.h5', 'w') as file:
            comp_type = np.dtype([('id', np.uint64), ('attr1', h5py.special_dtype(vlen=str))])
            test_ds = file.create_dataset(
                name='test_ds',
                data=np.array((1, 'text'), dtype=comp_type),
                shape=(1, ),
                dtype=comp_type
            )
            expected = BazScalarCompound(
                name='my_baz',
                data=(1, 'text'),
            )
            builder = DatasetBuilder(
                name='my_baz',
                data=test_ds,
                attributes={'data_type': 'BazScalarCompound',
                            'namespace': CORE_NAMESPACE,
                            'object_id': expected.object_id},
            )
            container = self.mapper.construct(builder, self.manager)
            self.assertEqual(type(container.data), h5py.Dataset)
            self.assertContainerEqual(container, expected)
        os.remove('test.h5')
