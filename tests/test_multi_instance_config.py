"""Tests for multi-instance configuration functionality."""

import os
from unittest.mock import patch

import pytest

from arrem_sync.config import ArrInstanceConfig, get_config


class TestMultiInstanceConfig:
    """Test multi-instance configuration parsing."""

    def test_single_numbered_instance(self):
        """Test single numbered instance configuration."""
        env_vars = {
            "ARREM_EMBY_URL": "http://localhost:8096",
            "ARREM_EMBY_API_KEY": "test_emby_key",
            "ARREM_ARR_1_TYPE": "radarr",
            "ARREM_ARR_1_URL": "http://localhost:7878",
            "ARREM_ARR_1_API_KEY": "test_radarr_key",
            "ARREM_ARR_1_NAME": "Main Radarr",
        }

        with patch.dict(os.environ, env_vars, clear=True), patch("arrem_sync.config.load_dotenv"):
            config = get_config()

            assert len(config.arr_instances) == 1
            instance = config.arr_instances[0]
            assert instance.type == "radarr"
            assert instance.url == "http://localhost:7878"
            assert instance.api_key == "test_radarr_key"
            assert instance.name == "Main Radarr"

    def test_multiple_numbered_instances(self):
        """Test multiple numbered instances configuration."""
        env_vars = {
            "ARREM_EMBY_URL": "http://localhost:8096",
            "ARREM_EMBY_API_KEY": "test_emby_key",
            "ARREM_ARR_1_TYPE": "radarr",
            "ARREM_ARR_1_URL": "http://localhost:7878",
            "ARREM_ARR_1_API_KEY": "test_radarr_key",
            "ARREM_ARR_1_NAME": "Main Radarr",
            "ARREM_ARR_2_TYPE": "sonarr",
            "ARREM_ARR_2_URL": "http://localhost:8989",
            "ARREM_ARR_2_API_KEY": "test_sonarr_key",
            "ARREM_ARR_2_NAME": "Main Sonarr",
            "ARREM_ARR_3_TYPE": "radarr",
            "ARREM_ARR_3_URL": "http://localhost:7879",
            "ARREM_ARR_3_API_KEY": "test_radarr2_key",
            "ARREM_ARR_3_NAME": "4K Radarr",
        }

        with patch.dict(os.environ, env_vars, clear=True), patch("arrem_sync.config.load_dotenv"):
            config = get_config()

            assert len(config.arr_instances) == 3

            # Check first instance
            instance1 = config.arr_instances[0]
            assert instance1.type == "radarr"
            assert instance1.url == "http://localhost:7878"
            assert instance1.api_key == "test_radarr_key"
            assert instance1.name == "Main Radarr"

            # Check second instance
            instance2 = config.arr_instances[1]
            assert instance2.type == "sonarr"
            assert instance2.url == "http://localhost:8989"
            assert instance2.api_key == "test_sonarr_key"
            assert instance2.name == "Main Sonarr"

            # Check third instance
            instance3 = config.arr_instances[2]
            assert instance3.type == "radarr"
            assert instance3.url == "http://localhost:7879"
            assert instance3.api_key == "test_radarr2_key"
            assert instance3.name == "4K Radarr"

    def test_no_instances_configured_error(self):
        """Test error when no Arr instances are configured."""
        env_vars = {
            "ARREM_EMBY_URL": "http://localhost:8096",
            "ARREM_EMBY_API_KEY": "test_emby_key",
        }

        with (
            patch.dict(os.environ, env_vars, clear=True),
            patch("arrem_sync.config.load_dotenv"),
            pytest.raises(ValueError, match="No Arr instances configured"),
        ):
            get_config()

    def test_incomplete_numbered_instance_skipped(self):
        """Test that incomplete numbered instances are skipped."""
        env_vars = {
            "ARREM_EMBY_URL": "http://localhost:8096",
            "ARREM_EMBY_API_KEY": "test_emby_key",
            "ARREM_ARR_1_TYPE": "radarr",
            "ARREM_ARR_1_URL": "http://localhost:7878",
            "ARREM_ARR_1_API_KEY": "test_radarr_key",
            # Incomplete instance 2 (missing API key)
            "ARREM_ARR_2_TYPE": "sonarr",
            "ARREM_ARR_2_URL": "http://localhost:8989",
            # Complete instance 3 (should be skipped due to gap)
            "ARREM_ARR_3_TYPE": "radarr",
            "ARREM_ARR_3_URL": "http://localhost:7879",
            "ARREM_ARR_3_API_KEY": "test_radarr2_key",
        }

        with patch.dict(os.environ, env_vars, clear=True), patch("arrem_sync.config.load_dotenv"):
            config = get_config()

            # Should only have instance 1 (instance 2 incomplete, instance 3 skipped due to gap)
            assert len(config.arr_instances) == 1
            instance = config.arr_instances[0]
            assert instance.type == "radarr"
            assert instance.url == "http://localhost:7878"

    def test_numbered_instances_without_names(self):
        """Test numbered instances without optional name field."""
        env_vars = {
            "ARREM_EMBY_URL": "http://localhost:8096",
            "ARREM_EMBY_API_KEY": "test_emby_key",
            "ARREM_ARR_1_TYPE": "radarr",
            "ARREM_ARR_1_URL": "http://localhost:7878",
            "ARREM_ARR_1_API_KEY": "test_radarr_key",
            # No ARREM_ARR_1_NAME specified
        }

        with patch.dict(os.environ, env_vars, clear=True), patch("arrem_sync.config.load_dotenv"):
            config = get_config()

            assert len(config.arr_instances) == 1
            instance = config.arr_instances[0]
            assert instance.type == "radarr"
            assert instance.url == "http://localhost:7878"
            assert instance.api_key == "test_radarr_key"
            assert instance.name is None


class TestArrInstanceConfig:
    """Test ArrInstanceConfig validation."""

    def test_valid_arr_instance_config(self):
        """Test valid ArrInstanceConfig creation."""
        config = ArrInstanceConfig(
            type="radarr",
            url="http://localhost:7878",
            api_key="test_key",
            name="Test Radarr",
        )

        assert config.type == "radarr"
        assert config.url == "http://localhost:7878"
        assert config.api_key == "test_key"
        assert config.name == "Test Radarr"

    def test_arr_instance_config_without_name(self):
        """Test ArrInstanceConfig creation without name."""
        config = ArrInstanceConfig(
            type="sonarr",
            url="http://localhost:8989",
            api_key="test_key",
        )

        assert config.type == "sonarr"
        assert config.url == "http://localhost:8989"
        assert config.api_key == "test_key"
        assert config.name is None

    def test_arr_instance_config_invalid_type(self):
        """Test ArrInstanceConfig with invalid arr_type."""
        with pytest.raises(ValueError, match="arr_type must be either 'radarr' or 'sonarr'"):
            ArrInstanceConfig(
                type="invalid",
                url="http://localhost:7878",
                api_key="test_key",
            )

    def test_arr_instance_config_case_insensitive_type(self):
        """Test ArrInstanceConfig with case-insensitive arr_type."""
        config = ArrInstanceConfig(
            type="RADARR",
            url="http://localhost:7878",
            api_key="test_key",
        )

        assert config.type == "radarr"  # Should be normalized to lowercase
