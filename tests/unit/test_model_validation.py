"""
Model Validation Service Unit Tests

Tests for ModelValidation module
"""
import unittest
from src.Model import ModelValidator, ModelValidationError, validate_parameters


class TestModelValidator(unittest.TestCase):
    """Test ModelValidator utility class"""

    def test_required_with_none(self):
        """Test required validation with None value"""
        with self.assertRaises(ModelValidationError) as cm:
            ModelValidator.required(None, "test_field")
        self.assertEqual(cm.exception.field, "test_field")
        self.assertEqual(cm.exception.value, None)

    def test_required_with_empty_string(self):
        """Test required validation with empty string"""
        with self.assertRaises(ModelValidationError):
            ModelValidator.required("", "test_field")

    def test_required_with_whitespace_string(self):
        """Test required validation with whitespace string"""
        with self.assertRaises(ModelValidationError):
            ModelValidator.required("   ", "test_field")

    def test_required_with_valid_value(self):
        """Test required validation with valid value"""
        # Should not raise exception
        ModelValidator.required("valid", "test_field")
        ModelValidator.required(0, "test_field")
        ModelValidator.required(False, "test_field")

    def test_numeric_range_min(self):
        """Test numeric range minimum validation"""
        with self.assertRaises(ModelValidationError):
            ModelValidator.numeric_range(5, "test_field", min_val=10)

        # Should not raise
        ModelValidator.numeric_range(10, "test_field", min_val=10)
        ModelValidator.numeric_range(15, "test_field", min_val=10)

    def test_numeric_range_max(self):
        """Test numeric range maximum validation"""
        with self.assertRaises(ModelValidationError):
            ModelValidator.numeric_range(15, "test_field", max_val=10)

        # Should not raise
        ModelValidator.numeric_range(10, "test_field", max_val=10)
        ModelValidator.numeric_range(5, "test_field", max_val=10)

    def test_numeric_range_both(self):
        """Test numeric range with both min and max"""
        with self.assertRaises(ModelValidationError):
            ModelValidator.numeric_range(0, "test_field", min_val=5, max_val=10)

        with self.assertRaises(ModelValidationError):
            ModelValidator.numeric_range(15, "test_field", min_val=5, max_val=10)

        # Should not raise
        ModelValidator.numeric_range(5, "test_field", min_val=5, max_val=10)
        ModelValidator.numeric_range(7, "test_field", min_val=5, max_val=10)
        ModelValidator.numeric_range(10, "test_field", min_val=5, max_val=10)

    def test_integer_conversion(self):
        """Test integer conversion"""
        self.assertEqual(ModelValidator.integer("123", "test_field"), 123)
        self.assertEqual(ModelValidator.integer(123.0, "test_field"), 123)
        self.assertEqual(ModelValidator.integer(123, "test_field"), 123)

    def test_integer_conversion_failure(self):
        """Test integer conversion with invalid value"""
        with self.assertRaises(ModelValidationError):
            ModelValidator.integer("not_a_number", "test_field")

    def test_float_conversion(self):
        """Test float conversion"""
        self.assertEqual(ModelValidator.float("123.45", "test_field"), 123.45)
        self.assertEqual(ModelValidator.float(123.45, "test_field"), 123.45)
        self.assertEqual(ModelValidator.float(123, "test_field"), 123.0)

    def test_float_conversion_failure(self):
        """Test float conversion with invalid value"""
        with self.assertRaises(ModelValidationError):
            ModelValidator.float("not_a_number", "test_field")

    def test_positive(self):
        """Test positive value validation"""
        with self.assertRaises(ModelValidationError):
            ModelValidator.positive(0, "test_field")

        with self.assertRaises(ModelValidationError):
            ModelValidator.positive(-5, "test_field")

        # Should not raise
        ModelValidator.positive(0.1, "test_field")
        ModelValidator.positive(100, "test_field")

    def test_non_negative(self):
        """Test non-negative value validation"""
        with self.assertRaises(ModelValidationError):
            ModelValidator.non_negative(-1, "test_field")

        # Should not raise
        ModelValidator.non_negative(0, "test_field")
        ModelValidator.non_negative(0.1, "test_field")
        ModelValidator.non_negative(100, "test_field")


class TestValidateParametersDecorator(unittest.TestCase):
    """Test validate_parameters decorator"""

    def test_decorator_with_valid_validator(self):
        """Test decorator with valid validator function"""

        def validator(params):
            return params.get("valid", False)

        class TestModel:
            @validate_parameters(validator)
            def test_method(self, params):
                return "success"

        model = TestModel()
        result = model.test_method({"valid": True})
        self.assertEqual(result, "success")

    def test_decorator_with_invalid_validator(self):
        """Test decorator with invalid validator function"""

        def validator(params):
            return False

        class TestModel:
            @validate_parameters(validator)
            def test_method(self, params):
                return "success"

        model = TestModel()
        with self.assertRaises(ModelValidationError):
            model.test_method({"valid": False})

    def test_decorator_with_exception_in_validator(self):
        """Test decorator when validator raises exception"""

        def validator(params):
            raise ValueError("Test error")

        class TestModel:
            @validate_parameters(validator)
            def test_method(self, params):
                return "success"

        model = TestModel()
        with self.assertRaises(ModelValidationError):
            model.test_method({})


if __name__ == '__main__':
    unittest.main()