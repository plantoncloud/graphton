"""Tests for template substitution engine.

This module tests the template variable extraction, substitution, and validation
utilities used for universal MCP authentication.
"""

import pytest

from graphton.core.template import (
    extract_template_vars,
    has_templates,
    substitute_templates,
    validate_template_syntax,
)


class TestExtractTemplateVars:
    """Tests for extract_template_vars function."""
    
    def test_extract_single_variable(self) -> None:
        """Test extracting a single template variable."""
        config = {"url": "https://api.example.com/{{API_KEY}}"}
        vars = extract_template_vars(config)
        assert vars == {"API_KEY"}
    
    def test_extract_multiple_variables(self) -> None:
        """Test extracting multiple template variables."""
        config = {
            "url": "{{BASE_URL}}/api",
            "headers": {
                "Authorization": "Bearer {{USER_TOKEN}}",
                "X-API-Key": "{{API_KEY}}"
            }
        }
        vars = extract_template_vars(config)
        assert vars == {"BASE_URL", "USER_TOKEN", "API_KEY"}
    
    def test_extract_from_nested_dict(self) -> None:
        """Test extracting variables from deeply nested dictionaries."""
        config = {
            "level1": {
                "level2": {
                    "level3": {
                        "token": "{{DEEP_TOKEN}}"
                    }
                }
            }
        }
        vars = extract_template_vars(config)
        assert vars == {"DEEP_TOKEN"}
    
    def test_extract_from_list(self) -> None:
        """Test extracting variables from lists."""
        config = {
            "urls": [
                "https://{{SERVER1}}/api",
                "https://{{SERVER2}}/api"
            ]
        }
        vars = extract_template_vars(config)
        assert vars == {"SERVER1", "SERVER2"}
    
    def test_extract_duplicate_variables(self) -> None:
        """Test that duplicate variables are deduplicated."""
        config = {
            "url1": "https://{{TOKEN}}/api",
            "url2": "https://{{TOKEN}}/v2"
        }
        vars = extract_template_vars(config)
        assert vars == {"TOKEN"}
    
    def test_extract_with_whitespace(self) -> None:
        """Test extracting variables with whitespace in braces."""
        config = {
            "token1": "{{ TOKEN_1 }}",
            "token2": "{{  TOKEN_2  }}"
        }
        vars = extract_template_vars(config)
        assert vars == {"TOKEN_1", "TOKEN_2"}
    
    def test_no_variables(self) -> None:
        """Test with config containing no template variables."""
        config = {
            "url": "https://api.example.com",
            "headers": {
                "Authorization": "Bearer hardcoded-token"
            }
        }
        vars = extract_template_vars(config)
        assert vars == set()
    
    def test_non_string_values(self) -> None:
        """Test with non-string values (should be ignored)."""
        config = {
            "port": 8080,
            "enabled": True,
            "timeout": None,
            "token": "{{TOKEN}}"
        }
        vars = extract_template_vars(config)
        assert vars == {"TOKEN"}
    
    def test_variable_name_with_numbers(self) -> None:
        """Test variable names with numbers."""
        config = {"key": "{{API_KEY_123}}"}
        vars = extract_template_vars(config)
        assert vars == {"API_KEY_123"}
    
    def test_variable_name_with_underscores(self) -> None:
        """Test variable names with underscores."""
        config = {"key": "{{MY_API_KEY}}"}
        vars = extract_template_vars(config)
        assert vars == {"MY_API_KEY"}


class TestHasTemplates:
    """Tests for has_templates function."""
    
    def test_has_templates_true(self) -> None:
        """Test that has_templates returns True when templates present."""
        config = {"url": "https://{{BASE_URL}}/api"}
        assert has_templates(config) is True
    
    def test_has_templates_false(self) -> None:
        """Test that has_templates returns False when no templates."""
        config = {"url": "https://api.example.com"}
        assert has_templates(config) is False
    
    def test_has_templates_empty_config(self) -> None:
        """Test with empty config."""
        config = {}
        assert has_templates(config) is False


class TestSubstituteTemplates:
    """Tests for substitute_templates function."""
    
    def test_substitute_single_variable(self) -> None:
        """Test substituting a single template variable."""
        config = {"url": "https://api.example.com/{{API_KEY}}"}
        values = {"API_KEY": "secret123"}
        result = substitute_templates(config, values)
        assert result["url"] == "https://api.example.com/secret123"
    
    def test_substitute_multiple_variables(self) -> None:
        """Test substituting multiple template variables."""
        config = {
            "url": "https://{{BASE_URL}}/api",
            "headers": {
                "Authorization": "Bearer {{USER_TOKEN}}",
                "X-API-Key": "{{API_KEY}}"
            }
        }
        values = {
            "BASE_URL": "api.example.com",
            "USER_TOKEN": "token123",
            "API_KEY": "key456"
        }
        result = substitute_templates(config, values)
        assert result["url"] == "https://api.example.com/api"
        assert result["headers"]["Authorization"] == "Bearer token123"
        assert result["headers"]["X-API-Key"] == "key456"
    
    def test_substitute_in_nested_dict(self) -> None:
        """Test substitution in deeply nested dictionaries."""
        config = {
            "level1": {
                "level2": {
                    "token": "{{DEEP_TOKEN}}"
                }
            }
        }
        values = {"DEEP_TOKEN": "secret"}
        result = substitute_templates(config, values)
        assert result["level1"]["level2"]["token"] == "secret"
    
    def test_substitute_in_list(self) -> None:
        """Test substitution in lists."""
        config = {
            "urls": [
                "https://{{SERVER1}}/api",
                "https://{{SERVER2}}/api"
            ]
        }
        values = {
            "SERVER1": "server1.example.com",
            "SERVER2": "server2.example.com"
        }
        result = substitute_templates(config, values)
        assert result["urls"][0] == "https://server1.example.com/api"
        assert result["urls"][1] == "https://server2.example.com/api"
    
    def test_substitute_with_whitespace(self) -> None:
        """Test substitution with whitespace in template."""
        config = {"token": "Bearer {{ TOKEN }}"}
        values = {"TOKEN": "abc123"}
        result = substitute_templates(config, values)
        assert result["token"] == "Bearer abc123"
    
    def test_substitute_missing_variable(self) -> None:
        """Test that missing variables raise ValueError."""
        config = {"token": "{{TOKEN}}"}
        values = {}  # TOKEN not provided
        
        with pytest.raises(ValueError, match="Missing required template variables: \\['TOKEN'\\]"):
            substitute_templates(config, values)
    
    def test_substitute_multiple_missing_variables(self) -> None:
        """Test error message for multiple missing variables."""
        config = {
            "token1": "{{TOKEN1}}",
            "token2": "{{TOKEN2}}",
            "token3": "{{TOKEN3}}"
        }
        values = {"TOKEN1": "value1"}  # TOKEN2 and TOKEN3 missing
        
        with pytest.raises(ValueError) as exc_info:
            substitute_templates(config, values)
        
        error_msg = str(exc_info.value)
        assert "TOKEN2" in error_msg
        assert "TOKEN3" in error_msg
    
    def test_substitute_preserves_non_template_values(self) -> None:
        """Test that non-template values are preserved unchanged."""
        config = {
            "port": 8080,
            "enabled": True,
            "timeout": None,
            "static_url": "https://api.example.com",
            "dynamic_token": "{{TOKEN}}"
        }
        values = {"TOKEN": "secret"}
        result = substitute_templates(config, values)
        
        assert result["port"] == 8080
        assert result["enabled"] is True
        assert result["timeout"] is None
        assert result["static_url"] == "https://api.example.com"
        assert result["dynamic_token"] == "secret"
    
    def test_substitute_multiple_variables_in_same_string(self) -> None:
        """Test substituting multiple variables in the same string."""
        config = {"url": "https://{{HOST}}:{{PORT}}/{{PATH}}"}
        values = {
            "HOST": "api.example.com",
            "PORT": "8443",
            "PATH": "v1/api"
        }
        result = substitute_templates(config, values)
        assert result["url"] == "https://api.example.com:8443/v1/api"
    
    def test_substitute_does_not_modify_original(self) -> None:
        """Test that substitution doesn't modify the original config."""
        config = {"token": "{{TOKEN}}"}
        values = {"TOKEN": "secret"}
        
        result = substitute_templates(config, values)
        
        # Original should be unchanged
        assert config["token"] == "{{TOKEN}}"
        # Result should have substitution
        assert result["token"] == "secret"
    
    def test_substitute_extra_values_ignored(self) -> None:
        """Test that extra values in values dict are ignored."""
        config = {"token": "{{TOKEN}}"}
        values = {
            "TOKEN": "secret",
            "EXTRA_VAR": "ignored"
        }
        result = substitute_templates(config, values)
        assert result["token"] == "secret"
        # EXTRA_VAR should not appear in result
        assert "EXTRA_VAR" not in result


class TestValidateTemplateSyntax:
    """Tests for validate_template_syntax function."""
    
    def test_valid_syntax(self) -> None:
        """Test validation passes for valid syntax."""
        config = {"token": "{{VALID_TOKEN}}"}
        errors = validate_template_syntax(config)
        assert errors == []
    
    def test_unbalanced_braces(self) -> None:
        """Test validation catches unbalanced braces."""
        config = {"token": "{{TOKEN}"}  # Missing closing brace
        errors = validate_template_syntax(config)
        assert len(errors) > 0
        assert "unbalanced braces" in errors[0].lower()
    
    def test_valid_non_template_braces(self) -> None:
        """Test that properly balanced non-template braces are valid."""
        config = {"json": '{"key": "value"}'}
        errors = validate_template_syntax(config)
        # This should pass - it's valid JSON, not a malformed template
        assert errors == []


class TestRealWorldScenarios:
    """Tests for real-world MCP configuration scenarios."""
    
    def test_planton_cloud_config(self) -> None:
        """Test Planton Cloud MCP server configuration."""
        config = {
            "planton-cloud": {
                "transport": "streamable_http",
                "url": "https://mcp.planton.ai/",
                "headers": {
                    "Authorization": "Bearer {{USER_TOKEN}}"
                }
            }
        }
        
        # Extract variables
        vars = extract_template_vars(config)
        assert vars == {"USER_TOKEN"}
        
        # Substitute
        values = {"USER_TOKEN": "pck_dK-AZOYaLuTZdbagAU12j6qhFsm8CWUFySpIdcijxUI"}
        result = substitute_templates(config, values)
        
        assert result["planton-cloud"]["headers"]["Authorization"] == \
            "Bearer pck_dK-AZOYaLuTZdbagAU12j6qhFsm8CWUFySpIdcijxUI"
    
    def test_multi_server_multi_auth(self) -> None:
        """Test configuration with multiple servers and different auth methods."""
        config = {
            "planton-cloud": {
                "transport": "streamable_http",
                "url": "https://mcp.planton.ai/",
                "headers": {
                    "Authorization": "Bearer {{USER_TOKEN}}"
                }
            },
            "external-api": {
                "transport": "http",
                "url": "{{BASE_URL}}/api",
                "headers": {
                    "X-API-Key": "{{API_KEY}}"
                }
            },
            "public-server": {
                "transport": "http",
                "url": "https://public.example.com",
                "headers": {
                    "X-Client-ID": "hardcoded-client-123"
                }
            }
        }
        
        # Extract variables (only from dynamic configs)
        vars = extract_template_vars(config)
        assert vars == {"USER_TOKEN", "BASE_URL", "API_KEY"}
        
        # Substitute
        values = {
            "USER_TOKEN": "token123",
            "BASE_URL": "https://api.example.com",
            "API_KEY": "key456"
        }
        result = substitute_templates(config, values)
        
        # Check dynamic substitutions
        assert "token123" in result["planton-cloud"]["headers"]["Authorization"]
        assert result["external-api"]["url"] == "https://api.example.com/api"
        assert result["external-api"]["headers"]["X-API-Key"] == "key456"
        
        # Check static values preserved
        assert result["public-server"]["url"] == "https://public.example.com"
        assert result["public-server"]["headers"]["X-Client-ID"] == "hardcoded-client-123"
    
    def test_static_config_no_templates(self) -> None:
        """Test completely static configuration with no templates."""
        config = {
            "public-api": {
                "transport": "http",
                "url": "https://api.example.com",
                "headers": {
                    "X-API-Key": "hardcoded-key-123"
                }
            }
        }
        
        # No variables
        assert not has_templates(config)
        assert extract_template_vars(config) == set()
        
        # Substitution with empty values should work
        result = substitute_templates(config, {})
        assert result == config














