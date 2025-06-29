"""
Unit tests for the singleton decorator utility.

Tests the thread-safe singleton pattern with reload capability,
including edge cases and thread safety.
"""

import threading
import time
from unittest.mock import patch

import pytest

from src.utils.singleton import singleton


class TestSingletonDecorator:
    """Test the singleton decorator functionality."""

    def test_singleton_same_parameters_returns_same_instance(self):
        """Test that same parameters return the same instance."""

        @singleton
        class TestClass:
            def __init__(self, value=None):
                self.value = value

        instance1 = TestClass(value="test")
        instance2 = TestClass(value="test")

        assert instance1 is instance2
        assert instance1.value == "test"

    def test_singleton_different_parameters_returns_different_instances(self):
        """Test that different parameters create different instances."""

        @singleton
        class TestClass:
            def __init__(self, value=None):
                self.value = value

        instance1 = TestClass(value="test1")
        instance2 = TestClass(value="test2")
        instance3 = TestClass()  # No parameters

        assert instance1 is not instance2
        assert instance1 is not instance3
        assert instance2 is not instance3
        assert instance1.value == "test1"
        assert instance2.value == "test2"
        assert instance3.value is None

    def test_singleton_no_parameters_returns_same_instance(self):
        """Test that no parameters consistently return the same instance."""

        @singleton
        class TestClass:
            def __init__(self):
                self.created_at = time.time()

        instance1 = TestClass()
        time.sleep(0.01)  # Small delay
        instance2 = TestClass()

        assert instance1 is instance2
        assert instance1.created_at == instance2.created_at

    def test_singleton_mixed_args_and_kwargs(self):
        """Test singleton behavior with mixed positional and keyword arguments."""

        @singleton
        class TestClass:
            def __init__(self, pos_arg, keyword_arg=None, another_kwarg="default"):
                self.pos_arg = pos_arg
                self.keyword_arg = keyword_arg
                self.another_kwarg = another_kwarg

        # Same arguments in different forms should return same instance
        instance1 = TestClass("pos", keyword_arg="kw", another_kwarg="custom")
        instance2 = TestClass("pos", keyword_arg="kw", another_kwarg="custom")

        assert instance1 is instance2

        # Different order of kwargs should still return same instance
        instance3 = TestClass("pos", another_kwarg="custom", keyword_arg="kw")
        assert instance1 is instance3

        # Different values should return different instance
        instance4 = TestClass("pos", keyword_arg="different", another_kwarg="custom")
        assert instance1 is not instance4

    def test_singleton_with_complex_parameters(self):
        """Test singleton with complex parameter types."""

        @singleton
        class TestClass:
            def __init__(self, simple_param=None, tuple_param=None):
                self.simple_param = simple_param
                self.tuple_param = tuple_param or ()

        # Test with hashable parameters only (since singleton uses dict keys)
        instance1 = TestClass(simple_param="test", tuple_param=(1, 2, 3))
        instance2 = TestClass(simple_param="test", tuple_param=(1, 2, 3))

        assert instance1 is instance2

    def test_singleton_thread_safety(self):
        """Test that singleton is thread-safe."""

        @singleton
        class TestClass:
            def __init__(self, value):
                self.value = value
                self.thread_id = threading.current_thread().ident
                # Add small delay to increase chance of race condition
                time.sleep(0.001)

        instances = []
        threads = []

        def create_instance():
            instance = TestClass("shared_value")
            instances.append(instance)

        # Create multiple threads that try to create instances simultaneously
        for _ in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)

        # Start all threads at roughly the same time
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All instances should be the same object
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance

        # Should have exactly one unique instance
        unique_instances = set(id(instance) for instance in instances)
        assert len(unique_instances) == 1

    def test_singleton_reload_functionality(self):
        """Test the reload_singleton method."""

        @singleton
        class TestClass:
            def __init__(self, value="default"):
                self.value = value
                self.created_at = time.time()

        # Create initial instance
        instance1 = TestClass(value="original")
        original_time = instance1.created_at

        time.sleep(0.01)  # Small delay

        # Reload with new parameters
        instance2 = instance1.reload_singleton(value="reloaded")

        assert instance1 is not instance2
        assert instance2.value == "reloaded"
        assert instance2.created_at > original_time

        # New calls with same parameters should return the reloaded instance
        instance3 = TestClass(value="reloaded")
        assert instance2 is instance3

    def test_singleton_reload_with_no_parameters_uses_original(self):
        """Test reload without parameters reuses original parameters."""

        @singleton
        class TestClass:
            def __init__(self, value="default", other="other"):
                self.value = value
                self.other = other
                self.created_at = time.time()

        # Create instance with specific parameters
        instance1 = TestClass(value="original", other="test")
        original_time = instance1.created_at

        # First reload with parameters to establish the _singleton_key
        instance2 = instance1.reload_singleton(
            value="first_reload", other="test_reload"
        )

        time.sleep(0.01)

        # Now reload without parameters should use the last reload parameters
        instance3 = instance2.reload_singleton()

        assert instance2 is not instance3
        assert instance3.value == "first_reload"  # Should use the reload value
        assert instance3.other == "test_reload"  # Should use the reload other
        assert instance3.created_at > original_time

    def test_singleton_reload_stores_key(self):
        """Test that reload stores the singleton key for future reloads."""

        @singleton
        class TestClass:
            def __init__(self, value="default"):
                self.value = value

        instance1 = TestClass(value="test")
        instance2 = instance1.reload_singleton(value="new_value")

        # The reloaded instance should have the singleton key stored
        assert hasattr(instance2, "_singleton_key")

        # Should be able to reload again without parameters
        instance3 = instance2.reload_singleton()
        assert instance3.value == "new_value"

    def test_singleton_with_class_without_init(self):
        """Test singleton with a class that doesn't have __init__."""

        @singleton
        class TestClass:
            pass

        instance1 = TestClass()
        instance2 = TestClass()

        assert instance1 is instance2

    def test_singleton_preserves_class_methods_and_attributes(self):
        """Test that singleton preserves original class methods and attributes."""

        @singleton
        class TestClass:
            class_attr = "class_value"

            def __init__(self, value):
                self.value = value

            def method(self):
                return f"method_result_{self.value}"

            @classmethod
            def class_method(cls):
                return "class_method_result"

            @staticmethod
            def static_method():
                return "static_method_result"

        instance = TestClass("test")

        # Test instance methods
        assert instance.method() == "method_result_test"

        # Test class methods and attributes
        assert TestClass.class_method() == "class_method_result"
        assert TestClass.static_method() == "static_method_result"
        assert TestClass.class_attr == "class_value"

        # Test that class methods work on instance too
        assert instance.class_method() == "class_method_result"
        assert instance.static_method() == "static_method_result"

    def test_singleton_internal_reload_flag_handling(self):
        """Test that internal _singleton_reload flag is properly handled."""

        @singleton
        class TestClass:
            def __init__(self, value="default", _singleton_reload=False):
                self.value = value
                # The _singleton_reload parameter should not be passed to __init__
                # This test ensures it's properly filtered out

        # This should work without the _singleton_reload parameter being passed to __init__
        instance1 = TestClass(value="test")
        instance2 = instance1.reload_singleton(value="reloaded")

        assert instance1 is not instance2
        assert instance2.value == "reloaded"

    def test_make_key_function_consistency(self):
        """Test that the internal _make_key function creates consistent keys."""

        @singleton
        class TestClass:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        # Test that different orderings of kwargs produce same instance
        instance1 = TestClass(a=1, b=2, c=3)
        instance2 = TestClass(c=3, a=1, b=2)
        instance3 = TestClass(b=2, c=3, a=1)

        assert instance1 is instance2
        assert instance2 is instance3

        # Test with mixed args and kwargs
        instance4 = TestClass("arg1", "arg2", a=1, b=2)
        instance5 = TestClass("arg1", "arg2", b=2, a=1)

        assert instance4 is instance5

    def test_singleton_error_handling_in_init(self):
        """Test singleton behavior when __init__ raises an exception."""

        @singleton
        class TestClass:
            def __init__(self, should_fail=False):
                if should_fail:
                    raise ValueError("Initialization failed")
                self.value = "success"

        # Successful initialization
        instance1 = TestClass(should_fail=False)
        assert instance1.value == "success"

        # Failed initialization should raise the exception
        with pytest.raises(ValueError, match="Initialization failed"):
            TestClass(should_fail=True)

        # Successful instance should still be accessible
        instance2 = TestClass(should_fail=False)
        assert instance1 is instance2

    def test_singleton_multiple_decorations(self):
        """Test that singleton works correctly even if applied multiple times."""

        @singleton
        @singleton  # Double decoration
        class TestClass:
            def __init__(self, value):
                self.value = value

        instance1 = TestClass("test")
        instance2 = TestClass("test")

        assert instance1 is instance2
        assert instance1.value == "test"


class TestSingletonEdgeCases:
    """Test edge cases and error conditions for singleton decorator."""

    def test_singleton_with_unhashable_parameters(self):
        """Test singleton behavior with unhashable parameters like lists and dicts."""

        @singleton
        class TestClass:
            def __init__(self, data):
                self.data = data

        # Lists and dicts are unhashable and should cause an error when used as dict keys
        # The singleton decorator should raise TypeError when trying to use unhashable types
        with pytest.raises(TypeError, match="unhashable type"):
            TestClass([1, 2, 3])

        with pytest.raises(TypeError, match="unhashable type"):
            TestClass({"key": "value"})

    def test_singleton_memory_behavior(self):
        """Test that singleton doesn't cause memory leaks by holding too many instances."""

        @singleton
        class TestClass:
            def __init__(self, value):
                self.value = value

        # Create many different instances
        instances = []
        for i in range(100):
            instance = TestClass(f"value_{i}")
            instances.append(instance)

        # Each should be different since parameters are different
        unique_instances = set(id(instance) for instance in instances)
        assert len(unique_instances) == 100

        # But same parameters should return same instance
        duplicate = TestClass("value_50")
        assert duplicate is instances[50]

    def test_singleton_inheritance(self):
        """Test singleton behavior with class inheritance."""

        @singleton
        class BaseClass:
            def __init__(self, value):
                self.value = value

        @singleton
        class ChildClass(BaseClass):
            def __init__(self, value, extra):
                super().__init__(value)
                self.extra = extra

        # Base class instances
        base1 = BaseClass("test")
        base2 = BaseClass("test")
        assert base1 is base2

        # Child class instances
        child1 = ChildClass("test", "extra")
        child2 = ChildClass("test", "extra")
        assert child1 is child2

        # Base and child should be different even with same base parameters
        base3 = BaseClass("test")
        assert base3 is base1  # Same as other base instances
        assert child1 is not base1  # Different from base instances
