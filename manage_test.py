#!/usr/bin/env python
"""
Simple test runner to run only the critical tests that validate our changes.
Skips broken dependencies and imports-at-module-load tests.
"""
import sys
import os
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
    
    # Run only the presenter tests we added
    failures = test_runner.run_tests([
        "empresa.tests.test_presenter.TestResumenPresenter",
        "empresa.tests.test_manufactura_presenter.TestManufacturaPresenter",
        "empresa.tests.test_comercio_presenter.ComercioPresenterTest",
        "empresa.tests.test_servicio_presenter.ServicioPresenterTest",
    ])
    
    sys.exit(bool(failures))
