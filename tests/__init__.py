# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

import pytest

pytest.register_assert_rewrite('tests.shared')
pytest.register_assert_rewrite('tests.commands.shared')
pytest.register_assert_rewrite('tests.libvirt.shared')
