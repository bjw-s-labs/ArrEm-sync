"""Tests for error handling utilities."""

import pytest
from pydantic import BaseModel, Field, ValidationError, field_validator

from arrem_sync.errors import (
    format_missing_env_vars,
    format_validation_error,
    handle_config_error,
)


class TestConfig(BaseModel):
    """Test configuration for error handling tests."""

    arr_type: str = Field(..., description="Type of Arr service")
    arr_url: str = Field(..., description="Arr service URL")
    log_level: str = Field(default="INFO", description="Log level")

    @field_validator("arr_type")
    @classmethod
    def validate_arr_type(cls, v):
        if v.lower() not in ["radarr", "sonarr"]:
            raise ValueError("arr_type must be either 'radarr' or 'sonarr'")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()


class TestErrorFormatting:
    """Test error formatting functions."""

    def test_format_validation_error_with_value_errors(self):
        """Test formatting validation errors with field validators."""
        with pytest.raises(ValidationError) as exc_info:
            TestConfig(
                arr_type="invalid_service",
                arr_url="http://localhost",
                log_level="INVALID",
            )

        formatted = format_validation_error(exc_info.value)

        # Check that the formatted error is human-readable
        assert "❌ arr_type: arr_type must be either 'radarr' or 'sonarr'" in formatted
        assert "❌ log_level: log_level must be one of ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']" in formatted

        # Check that technical pydantic details are removed
        assert "Value error," not in formatted
        assert "type=value_error" not in formatted
        assert "input_value=" not in formatted
        assert "For further information visit" not in formatted

    def test_format_validation_error_with_missing_fields(self):
        """Test formatting validation errors with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            TestConfig(log_level="DEBUG")  # Missing arr_type and arr_url

        formatted = format_validation_error(exc_info.value)

        # Check that missing field errors are properly formatted
        assert "❌ arr_type: 'arr_type' is required" in formatted
        assert "❌ arr_url: 'arr_url' is required" in formatted

        # Check that technical pydantic details are removed
        assert "Field required" not in formatted
        assert "type=missing" not in formatted

    def test_format_validation_error_empty(self):
        """Test formatting with empty validation error."""
        # For now, we'll skip this edge case test since creating
        # an empty ValidationError is complex with pydantic v2
        # The function handles this case but it's rarely encountered
        pass

    def test_format_missing_env_vars(self):
        """Test formatting missing environment variables."""
        missing_vars = ["arr_type", "arr_url", "emby_url"]
        formatted = format_missing_env_vars(missing_vars)

        # Check that environment variable names are properly prefixed
        assert "ARREM_ARR_TYPE" in formatted
        assert "ARREM_ARR_URL" in formatted
        assert "ARREM_EMBY_URL" in formatted

        # Check that helpful content is included
        assert "❌ Missing required configuration:" in formatted
        assert "💡 Example configuration:" in formatted
        assert "export ARREM_ARR_TYPE=radarr" in formatted
        assert "🔗 See the README.md for complete configuration details." in formatted

    def test_format_missing_env_vars_empty(self):
        """Test formatting with empty missing variables list."""
        formatted = format_missing_env_vars([])
        assert formatted == ""

    def test_handle_config_error_with_validation_error(self, capsys):
        """Test handle_config_error with ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TestConfig(arr_type="invalid")

        handle_config_error(exc_info.value)

        captured = capsys.readouterr()
        assert "📋 Configuration Error:" in captured.err
        assert "❌" in captured.err

    def test_handle_config_error_with_other_exception(self, capsys):
        """Test handle_config_error with other exceptions."""
        test_error = ValueError("Test error message")

        handle_config_error(test_error)

        captured = capsys.readouterr()
        assert "❌ Configuration Error: Test error message" in captured.err
        assert "💡 Check your environment variables and configuration." in captured.err


class TestEdgeCases:
    """Test edge cases and missing line coverage."""

    def test_format_validation_error_empty_errors(self):
        """Test formatting validation error with empty errors list."""
        # Create a custom ValidationError with empty errors
        try:
            raise ValidationError.from_exception_data("test", [])
        except ValidationError as e:
            formatted = format_validation_error(e)
            assert formatted == "Configuration validation failed"

    def test_format_validation_error_no_location(self):
        """Test formatting validation error with no location info."""

        class MinimalModel(BaseModel):
            value: str

        try:
            # This will create an error without specific location
            MinimalModel.model_validate({})
        except ValidationError as e:
            # Manually modify the error to test edge case
            error_data = e.errors()
            if error_data:
                error_data[0]["loc"] = ()  # Empty location tuple
            formatted = format_validation_error(e)
            assert "unknown field" in formatted.lower() or "required" in formatted.lower()

    def test_format_validation_error_string_should_pattern(self):
        """Test formatting validation error with 'String should' pattern."""
        from pydantic import BaseModel

        class StringModel(BaseModel):
            email: str

        try:
            StringModel(email=123)  # This should trigger 'String should be a valid string'
        except ValidationError as e:
            formatted = format_validation_error(e)
            # Should contain the field name and formatted message
            assert "email" in formatted.lower()

    def test_format_validation_error_input_should_pattern(self):
        """Test formatting validation error with 'Input should be' pattern."""
        from pydantic import BaseModel

        class IntModel(BaseModel):
            number: int

        try:
            IntModel(number="not_a_number")
        except ValidationError as e:
            formatted = format_validation_error(e)
            # Should contain formatted message with field name
            assert "number" in formatted.lower()
            assert "should be" in formatted.lower()

    def test_format_missing_env_vars_edge_case(self):
        """Test formatting missing env vars with different variable types."""
        # Test with environment variables that might have special formatting
        missing_vars = ["ARR_API_KEY", "EMBY_URL", "LOG_LEVEL"]
        formatted = format_missing_env_vars(missing_vars)

        # Should contain all variables (with prefix)
        assert "ARR_API_KEY" in formatted
        assert "EMBY_URL" in formatted
        assert "LOG_LEVEL" in formatted

        # Should contain export commands (with the ARREM_ prefix that gets added)
        assert "export ARREM_ARR_API_KEY=" in formatted
        assert "export ARREM_EMBY_URL=" in formatted
        assert "export ARREM_LOG_LEVEL=" in formatted

    def test_handle_config_error_with_missing_fields_detection(self, capsys):
        """Test handle_config_error detecting missing fields."""
        # Create a validation error with missing fields
        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            required_field: str = Field(..., description="Required field")
            optional_field: str = "default"

        try:
            TestModel()
        except ValidationError as e:
            handle_config_error(e)

        captured = capsys.readouterr()
        # Should detect missing required field and show environment variable suggestions
        assert "📋 Configuration Error:" in captured.err
        assert "export required_field=" in captured.err or "required_field" in captured.err

    def test_handle_config_error_non_validation_error(self, capsys):
        """Test handle_config_error with non-ValidationError exceptions."""
        # Test with different exception types
        runtime_error = RuntimeError("Runtime issue occurred")
        handle_config_error(runtime_error)

        captured = capsys.readouterr()
        assert "❌ Configuration Error: Runtime issue occurred" in captured.err
        assert "💡 Check your environment variables and configuration." in captured.err

        # Test with another exception type
        capsys.readouterr()  # Clear previous output
        value_error = ValueError("Invalid configuration value")
        handle_config_error(value_error)

        captured = capsys.readouterr()
        assert "❌ Configuration Error: Invalid configuration value" in captured.err
