 For further information visit https://errors.pydantic.dev/2.13/v/uuid_type

tests/integration/test_sensor_sync.py:246: ValidationError
___________________________________________________ test_sensor_history_filter_by_parameter ____________________________________________________

client = <httpx.AsyncClient object at 0x7474b87b4950>
sample_sensor_readings = [<SensorReading(sensor_id=bec17ba9-d741-43dc-aaee-56d104b1eff8, recorded_at=2026-05-18 10:00:00+00:00)>, <SensorReadin...:00:00+00:00)>, <SensorReading(sensor_id=8f72c152-0b3a-4f39-a47e-5e8fe333eb85, recorded_at=2026-05-18 10:00:00+00:00)>]

    @pytest.mark.asyncio
    async def test_sensor_history_filter_by_parameter(client, sample_sensor_readings):
        """Test filtering sensor history by parameter_name."""
        params = {"parameter_name": "temperature"}
    
        response = await client.get("/api/v1/sensors/history", params=params)
    
        assert response.status_code == 200
        data = response.json()
>       assert data["count"] == 3  # 2 from Line-A + 1 from Line-B
        ^^^^^^^^^^^^^^^^^^^^^^^^^
E       assert 0 == 3

tests/integration/test_sensors_routes.py:157: AssertionError
------------------------------------------------------------- Captured stdout call -------------------------------------------------------------
2026-05-19T10:33:38.133432Z [info     ] http_request_started           [app.middleware.logging] client_host=127.0.0.1 content_length=None content_type=None method=GET path=/api/v1/sensors/history query='parameter_name=temperature' service='Dashboard Analytics API' service_version=1.0.0 trace_id=753c5d48-dc7f-45 user_agent=python-httpx/0.28.1
2026-05-19T10:33:38.145282Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=11.76 memory={'rss_mb': 171.2, 'vms_mb': 842.05} method=GET path=/api/v1/sensors/history response_content_length=22 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=753c5d48-dc7f-45
HTTP Request: GET http://test/api/v1/sensors/history?parameter_name=temperature "HTTP/1.1 200 OK"
-------------------------------------------------------------- Captured log call ---------------------------------------------------------------
INFO     app.middleware.logging:logging.py:49 2026-05-19T10:33:38.133432Z [info     ] http_request_started           [app.middleware.logging] client_host=127.0.0.1 content_length=None content_type=None method=GET path=/api/v1/sensors/history query='parameter_name=temperature' service='Dashboard Analytics API' service_version=1.0.0 trace_id=753c5d48-dc7f-45 user_agent=python-httpx/0.28.1
INFO     app.middleware.logging:logging.py:81 2026-05-19T10:33:38.145282Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=11.76 memory={'rss_mb': 171.2, 'vms_mb': 842.05} method=GET path=/api/v1/sensors/history response_content_length=22 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=753c5d48-dc7f-45
INFO     httpx:_client.py:1740 HTTP Request: GET http://test/api/v1/sensors/history?parameter_name=temperature "HTTP/1.1 200 OK"
_____________________________________________________ test_sensor_alerts_only_bad_quality ______________________________________________________

client = <httpx.AsyncClient object at 0x7474b83ced20>
sample_sensor_readings = [<SensorReading(sensor_id=0634a450-791e-4a55-8cc3-967375b863d0, recorded_at=2026-05-18 10:00:00+00:00)>, <SensorReadin...:00:00+00:00)>, <SensorReading(sensor_id=d886a56d-c909-4727-bfba-5b45b92433a7, recorded_at=2026-05-18 10:00:00+00:00)>]

    @pytest.mark.asyncio
    async def test_sensor_alerts_only_bad_quality(client, sample_sensor_readings):
        """Test that alerts only returns BAD or DEGRADED quality readings."""
        response = await client.get("/api/v1/sensors/alerts")
    
        assert response.status_code == 200
        data = response.json()
>       assert data["count"] == 2  # 1 BAD + 1 DEGRADED
        ^^^^^^^^^^^^^^^^^^^^^^^^^
E       assert 0 == 2

tests/integration/test_sensors_routes.py:209: AssertionError
------------------------------------------------------------- Captured stdout call -------------------------------------------------------------
2026-05-19T10:33:43.343356Z [info     ] http_request_started           [app.middleware.logging] client_host=127.0.0.1 content_length=None content_type=None method=GET path=/api/v1/sensors/alerts query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=b479d613-94d6-40 user_agent=python-httpx/0.28.1
2026-05-19T10:33:43.362969Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=19.47 memory={'rss_mb': 171.5, 'vms_mb': 842.18} method=GET path=/api/v1/sensors/alerts response_content_length=22 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=b479d613-94d6-40
HTTP Request: GET http://test/api/v1/sensors/alerts "HTTP/1.1 200 OK"
-------------------------------------------------------------- Captured log call ---------------------------------------------------------------
INFO     app.middleware.logging:logging.py:49 2026-05-19T10:33:43.343356Z [info     ] http_request_started           [app.middleware.logging] client_host=127.0.0.1 content_length=None content_type=None method=GET path=/api/v1/sensors/alerts query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=b479d613-94d6-40 user_agent=python-httpx/0.28.1
INFO     app.middleware.logging:logging.py:81 2026-05-19T10:33:43.362969Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=19.47 memory={'rss_mb': 171.5, 'vms_mb': 842.18} method=GET path=/api/v1/sensors/alerts response_content_length=22 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=b479d613-94d6-40
INFO     httpx:_client.py:1740 HTTP Request: GET http://test/api/v1/sensors/alerts "HTTP/1.1 200 OK"
________________________________________________________ test_sensor_stats_alert_count _________________________________________________________

client = <httpx.AsyncClient object at 0x7474b8048860>
sample_sensor_readings = [<SensorReading(sensor_id=bb4a4d6e-39cd-4539-a637-1f4d1f7bbdc0, recorded_at=2026-05-18 10:00:00+00:00)>, <SensorReadin...:00:00+00:00)>, <SensorReading(sensor_id=f75f7c64-9fad-4aa5-81c8-4d4c5a3a93c4, recorded_at=2026-05-18 10:00:00+00:00)>]

    @pytest.mark.asyncio
    async def test_sensor_stats_alert_count(client, sample_sensor_readings):
        """Test that alert_count correctly counts BAD/DEGRADED readings."""
        response = await client.get("/api/v1/sensors/stats")
    
        assert response.status_code == 200
        data = response.json()
        total_alerts = sum(item["alert_count"] for item in data["items"])
>       assert total_alerts == 2  # 1 BAD + 1 DEGRADED across all lines
        ^^^^^^^^^^^^^^^^^^^^^^^^
E       assert 0 == 2

tests/integration/test_sensors_routes.py:271: AssertionError
------------------------------------------------------------- Captured stdout call -------------------------------------------------------------
2026-05-19T10:33:50.936347Z [info     ] http_request_started           [app.middleware.logging] client_host=127.0.0.1 content_length=None content_type=None method=GET path=/api/v1/sensors/stats query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=e63c6886-7337-4c user_agent=python-httpx/0.28.1
2026-05-19T10:33:50.954053Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=17.41 memory={'rss_mb': 172.49, 'vms_mb': 843.29} method=GET path=/api/v1/sensors/stats response_content_length=763 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=e63c6886-7337-4c
HTTP Request: GET http://test/api/v1/sensors/stats "HTTP/1.1 200 OK"
-------------------------------------------------------------- Captured log call ---------------------------------------------------------------
INFO     app.middleware.logging:logging.py:49 2026-05-19T10:33:50.936347Z [info     ] http_request_started           [app.middleware.logging] client_host=127.0.0.1 content_length=None content_type=None method=GET path=/api/v1/sensors/stats query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=e63c6886-7337-4c user_agent=python-httpx/0.28.1
INFO     app.middleware.logging:logging.py:81 2026-05-19T10:33:50.954053Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=17.41 memory={'rss_mb': 172.49, 'vms_mb': 843.29} method=GET path=/api/v1/sensors/stats response_content_length=763 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=e63c6886-7337-4c
INFO     httpx:_client.py:1740 HTTP Request: GET http://test/api/v1/sensors/stats "HTTP/1.1 200 OK"
_______________________________________________ test_compare_kpi_defect_rate_change_calculation ________________________________________________

session = <sqlalchemy.ext.asyncio.session.AsyncSession object at 0x7474b3ff3d70>

    @pytest.mark.asyncio
    async def test_compare_kpi_defect_rate_change_calculation(session):
        """Test that defect rate change is correctly calculated as difference."""
        today = date.today()
    
>       kpi1 = AggregatedKPI(
            period_from=today - timedelta(days=30),
            period_to=today,
            production_line=None,
            total_output=Decimal("1000"),
            defect_rate=Decimal("3.0"),
            completed_orders=50,
            total_orders=100,
            oee_estimate=Decimal("85.0")
        )

tests/unit/test_kpi_service.py:243: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
<string>:4: in __init__
    ???
.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:596: in _initialize_instance
    with util.safe_reraise():
.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py:121: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:594: in _initialize_instance
    manager.original_init(*mixed[1:], **kwargs)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <AggregatedKPI(2026-04-19 to 2026-05-19, line=None)>
kwargs = {'completed_orders': 50, 'defect_rate': Decimal('3.0'), 'oee_estimate': Decimal('85.0'), 'period_from': datetime.date(2026, 4, 19), ...}
cls_ = <class 'app.models.kpi.AggregatedKPI'>, k = 'production_line'

    def _declarative_constructor(self: Any, **kwargs: Any) -> None:
        """A simple constructor that allows initialization from kwargs.
    
        Sets attributes on the constructed instance using the names and
        values in ``kwargs``.
    
        Only keys that are present as
        attributes of the instance's class are allowed. These could be,
        for example, any mapped columns or relationships.
        """
        cls_ = type(self)
        for k in kwargs:
            if not hasattr(cls_, k):
>               raise TypeError(
                    "%r is an invalid keyword argument for %s" % (k, cls_.__name__)
                )
E               TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI

.venv/lib/python3.12/site-packages/sqlalchemy/orm/decl_base.py:2179: TypeError
_____________________________________________ test_compare_kpi_order_completion_change_calculation _____________________________________________

session = <sqlalchemy.ext.asyncio.session.AsyncSession object at 0x7474b80e4cb0>

    @pytest.mark.asyncio
    async def test_compare_kpi_order_completion_change_calculation(session):
        """Test that order completion rate change is correctly calculated."""
        today = date.today()
    
        # Period 1: 60% completion (60/100)
>       kpi1 = AggregatedKPI(
            period_from=today - timedelta(days=30),
            period_to=today,
            production_line=None,
            total_output=Decimal("1000"),
            defect_rate=Decimal("2.5"),
            completed_orders=60,
            total_orders=100,
            oee_estimate=Decimal("85.0")
        )

tests/unit/test_kpi_service.py:286: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
<string>:4: in __init__
    ???
.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:596: in _initialize_instance
    with util.safe_reraise():
.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py:121: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:594: in _initialize_instance
    manager.original_init(*mixed[1:], **kwargs)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <AggregatedKPI(2026-04-19 to 2026-05-19, line=None)>
kwargs = {'completed_orders': 60, 'defect_rate': Decimal('2.5'), 'oee_estimate': Decimal('85.0'), 'period_from': datetime.date(2026, 4, 19), ...}
cls_ = <class 'app.models.kpi.AggregatedKPI'>, k = 'production_line'

    def _declarative_constructor(self: Any, **kwargs: Any) -> None:
        """A simple constructor that allows initialization from kwargs.
    
        Sets attributes on the constructed instance using the names and
        values in ``kwargs``.
    
        Only keys that are present as
        attributes of the instance's class are allowed. These could be,
        for example, any mapped columns or relationships.
        """
        cls_ = type(self)
        for k in kwargs:
            if not hasattr(cls_, k):
>               raise TypeError(
                    "%r is an invalid keyword argument for %s" % (k, cls_.__name__)
                )
E               TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI

.venv/lib/python3.12/site-packages/sqlalchemy/orm/decl_base.py:2179: TypeError
___________________________________________________ test_compare_kpi_with_zero_total_orders ____________________________________________________

session = <sqlalchemy.ext.asyncio.session.AsyncSession object at 0x7474b3cc7f50>

    @pytest.mark.asyncio
    async def test_compare_kpi_with_zero_total_orders(session):
        """Test comparison handles zero total orders gracefully."""
        today = date.today()
    
>       kpi_zero_orders = AggregatedKPI(
            period_from=today - timedelta(days=30),
            period_to=today,
            production_line=None,
            total_output=Decimal("0"),
            defect_rate=Decimal("0"),
            completed_orders=0,
            total_orders=0,  # Zero orders
            oee_estimate=None
        )

tests/unit/test_kpi_service.py:329: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
<string>:4: in __init__
    ???
.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:596: in _initialize_instance
    with util.safe_reraise():
.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py:121: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:594: in _initialize_instance
    manager.original_init(*mixed[1:], **kwargs)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <AggregatedKPI(2026-04-19 to 2026-05-19, line=None)>
kwargs = {'completed_orders': 0, 'defect_rate': Decimal('0'), 'oee_estimate': None, 'period_from': datetime.date(2026, 4, 19), ...}
cls_ = <class 'app.models.kpi.AggregatedKPI'>, k = 'production_line'

    def _declarative_constructor(self: Any, **kwargs: Any) -> None:
        """A simple constructor that allows initialization from kwargs.
    
        Sets attributes on the constructed instance using the names and
        values in ``kwargs``.
    
        Only keys that are present as
        attributes of the instance's class are allowed. These could be,
        for example, any mapped columns or relationships.
        """
        cls_ = type(self)
        for k in kwargs:
            if not hasattr(cls_, k):
>               raise TypeError(
                    "%r is an invalid keyword argument for %s" % (k, cls_.__name__)
                )
E               TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI

.venv/lib/python3.12/site-packages/sqlalchemy/orm/decl_base.py:2179: TypeError
____________________________________________________ test_root_endpoint_has_response_model _____________________________________________________

openapi_spec = {'components': {'schemas': {'BatchAnalysisItem': {'description': 'A lot that had at least one out-of-spec result, with.....}, 'description': 'Successful Response'}, '422': {'content': {...}, 'description': 'Validation Error'}}, ...}}, ...}}

    def test_root_endpoint_has_response_model(openapi_spec):
        """Root endpoint must have response_model defined."""
        paths = openapi_spec.get("paths", {})
        root = paths.get("/", {})
        get_op = root.get("get", {})
    
        assert get_op, "GET / endpoint must exist"
        assert "responses" in get_op
        assert "200" in get_op["responses"]
    
        response_content = get_op["responses"]["200"]
        if "$ref" in response_content:
            return
    
        content = response_content.get("content", {})
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
>           assert "$ref" in schema, "Root endpoint must have response_model (schema ref)"
E           AssertionError: Root endpoint must have response_model (schema ref)
E           assert '$ref' in {}

tests/unit/test_openapi_contract.py:61: AssertionError
------------------------------------------------------------ Captured stdout setup -------------------------------------------------------------
2026-05-19T10:35:25.157375Z [info     ] http_request_started           [app.middleware.logging] client_host=testclient content_length=None content_type=None method=GET path=/openapi.json query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=aba2e7eb-9f3e-4f user_agent=testclient
2026-05-19T10:35:25.162247Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=4.64 memory={'rss_mb': 190.04, 'vms_mb': 859.0} method=GET path=/openapi.json response_content_length=149458 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=aba2e7eb-9f3e-4f
HTTP Request: GET http://testserver/openapi.json "HTTP/1.1 200 OK"
-------------------------------------------------------------- Captured log setup --------------------------------------------------------------
INFO     app.middleware.logging:logging.py:49 2026-05-19T10:35:25.157375Z [info     ] http_request_started           [app.middleware.logging] client_host=testclient content_length=None content_type=None method=GET path=/openapi.json query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=aba2e7eb-9f3e-4f user_agent=testclient
INFO     app.middleware.logging:logging.py:81 2026-05-19T10:35:25.162247Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=4.64 memory={'rss_mb': 190.04, 'vms_mb': 859.0} method=GET path=/openapi.json response_content_length=149458 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=aba2e7eb-9f3e-4f
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/openapi.json "HTTP/1.1 200 OK"
___________________________________________________ test_inventory_trends_has_response_model ___________________________________________________

openapi_spec = {'components': {'schemas': {'BatchAnalysisItem': {'description': 'A lot that had at least one out-of-spec result, with.....}, 'description': 'Successful Response'}, '422': {'content': {...}, 'description': 'Validation Error'}}, ...}}, ...}}

    def test_inventory_trends_has_response_model(openapi_spec):
        """Inventory trends endpoint must have response_model."""
        paths = openapi_spec.get("paths", {})
        trends = paths.get("/api/v1/inventory/trends", {})
        get_op = trends.get("get", {})
    
        assert get_op, "GET /api/v1/inventory/trends must exist"
        assert "responses" in get_op
    
        response_content = get_op["responses"].get("200", {})
        if "$ref" in response_content:
            return
    
        content = response_content.get("content", {})
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
>           assert "$ref" in schema, "Inventory trends must have response_model"
E           AssertionError: Inventory trends must have response_model
E           assert '$ref' in {}

tests/unit/test_openapi_contract.py:80: AssertionError
------------------------------------------------------------ Captured stdout setup -------------------------------------------------------------
2026-05-19T10:35:25.181640Z [info     ] http_request_started           [app.middleware.logging] client_host=testclient content_length=None content_type=None method=GET path=/openapi.json query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=08e09202-bf23-4c user_agent=testclient
2026-05-19T10:35:25.186619Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=4.71 memory={'rss_mb': 190.04, 'vms_mb': 859.0} method=GET path=/openapi.json response_content_length=149458 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=08e09202-bf23-4c
HTTP Request: GET http://testserver/openapi.json "HTTP/1.1 200 OK"
-------------------------------------------------------------- Captured log setup --------------------------------------------------------------
INFO     app.middleware.logging:logging.py:49 2026-05-19T10:35:25.181640Z [info     ] http_request_started           [app.middleware.logging] client_host=testclient content_length=None content_type=None method=GET path=/openapi.json query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=08e09202-bf23-4c user_agent=testclient
INFO     app.middleware.logging:logging.py:81 2026-05-19T10:35:25.186619Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=4.71 memory={'rss_mb': 190.04, 'vms_mb': 859.0} method=GET path=/openapi.json response_content_length=149458 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=08e09202-bf23-4c
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/openapi.json "HTTP/1.1 200 OK"
____________________________________________________ test_sensors_stats_has_response_model _____________________________________________________

openapi_spec = {'components': {'schemas': {'BatchAnalysisItem': {'description': 'A lot that had at least one out-of-spec result, with.....}, 'description': 'Successful Response'}, '422': {'content': {...}, 'description': 'Validation Error'}}, ...}}, ...}}

    def test_sensors_stats_has_response_model(openapi_spec):
        """Sensors stats endpoint must have response_model."""
        paths = openapi_spec.get("paths", {})
        stats = paths.get("/api/v1/sensors/stats", {})
        get_op = stats.get("get", {})
    
        assert get_op, "GET /api/v1/sensors/stats must exist"
        assert "responses" in get_op
    
        response_content = get_op["responses"].get("200", {})
        if "$ref" in response_content:
            return
    
        content = response_content.get("content", {})
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
>           assert "$ref" in schema, "Sensors stats must have response_model"
E           AssertionError: Sensors stats must have response_model
E           assert '$ref' in {}

tests/unit/test_openapi_contract.py:99: AssertionError
------------------------------------------------------------ Captured stdout setup -------------------------------------------------------------
2026-05-19T10:35:25.205762Z [info     ] http_request_started           [app.middleware.logging] client_host=testclient content_length=None content_type=None method=GET path=/openapi.json query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=b4b12364-c0e8-40 user_agent=testclient
2026-05-19T10:35:25.210844Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=4.83 memory={'rss_mb': 190.04, 'vms_mb': 859.0} method=GET path=/openapi.json response_content_length=149458 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=b4b12364-c0e8-40
HTTP Request: GET http://testserver/openapi.json "HTTP/1.1 200 OK"
-------------------------------------------------------------- Captured log setup --------------------------------------------------------------
INFO     app.middleware.logging:logging.py:49 2026-05-19T10:35:25.205762Z [info     ] http_request_started           [app.middleware.logging] client_host=testclient content_length=None content_type=None method=GET path=/openapi.json query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=b4b12364-c0e8-40 user_agent=testclient
INFO     app.middleware.logging:logging.py:81 2026-05-19T10:35:25.210844Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=4.83 memory={'rss_mb': 190.04, 'vms_mb': 859.0} method=GET path=/openapi.json response_content_length=149458 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=b4b12364-c0e8-40
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/openapi.json "HTTP/1.1 200 OK"
___________________________________________________ test_all_endpoints_have_response_models ____________________________________________________

openapi_spec = {'components': {'schemas': {'BatchAnalysisItem': {'description': 'A lot that had at least one out-of-spec result, with.....}, 'description': 'Successful Response'}, '422': {'content': {...}, 'description': 'Validation Error'}}, ...}}, ...}}

    def test_all_endpoints_have_response_models(openapi_spec):
        """All GET endpoints should have 200 response with schema."""
        paths = openapi_spec.get("paths", {})
    
        endpoints_without_response = []
    
        for path, methods in paths.items():
            if "get" in methods:
                get_op = methods["get"]
                responses = get_op.get("responses", {})
    
                if "200" not in responses:
                    endpoints_without_response.append(path)
                    continue
    
                response_200 = responses.get("200", {})
    
                if "$ref" in response_200:
                    continue
    
                content = response_200.get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    if "$ref" not in schema:
                        endpoints_without_response.append(path)
    
>       assert not endpoints_without_response, (
            f"Endpoints without response_model: {endpoints_without_response}"
        )
E       AssertionError: Endpoints without response_model: ['/', '/api/v1/sync/running', '/api/v1/products', '/api/v1/products/{product_id}', '/api/v1/output/summary', '/api/v1/output/by-shift', '/api/v1/sensors/history', '/api/v1/sensors/alerts', '/api/v1/sensors/stats', '/api/v1/inventory/current', '/api/v1/inventory/trends', '/api/production/kpi/debug/date-range', '/api/v1/export/gm', '/api/v1/export/finance', '/api/v1/export/qe', '/api/v1/export/production-overview', '/api/v1/export/line-master']
E       assert not ['/', '/api/v1/sync/running', '/api/v1/products', '/api/v1/products/{product_id}', '/api/v1/output/summary', '/api/v1/output/by-shift', ...]

tests/unit/test_openapi_contract.py:128: AssertionError
------------------------------------------------------------ Captured stdout setup -------------------------------------------------------------
2026-05-19T10:35:25.227327Z [info     ] http_request_started           [app.middleware.logging] client_host=testclient content_length=None content_type=None method=GET path=/openapi.json query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=8a3f2459-a8b9-49 user_agent=testclient
2026-05-19T10:35:25.232217Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=4.71 memory={'rss_mb': 190.11, 'vms_mb': 859.0} method=GET path=/openapi.json response_content_length=149458 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=8a3f2459-a8b9-49
HTTP Request: GET http://testserver/openapi.json "HTTP/1.1 200 OK"
-------------------------------------------------------------- Captured log setup --------------------------------------------------------------
INFO     app.middleware.logging:logging.py:49 2026-05-19T10:35:25.227327Z [info     ] http_request_started           [app.middleware.logging] client_host=testclient content_length=None content_type=None method=GET path=/openapi.json query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=8a3f2459-a8b9-49 user_agent=testclient
INFO     app.middleware.logging:logging.py:81 2026-05-19T10:35:25.232217Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=4.71 memory={'rss_mb': 190.11, 'vms_mb': 859.0} method=GET path=/openapi.json response_content_length=149458 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=8a3f2459-a8b9-49
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/openapi.json "HTTP/1.1 200 OK"
__________________________________________________________ test_schemas_have_examples __________________________________________________________

openapi_spec = {'components': {'schemas': {'BatchAnalysisItem': {'description': 'A lot that had at least one out-of-spec result, with.....}, 'description': 'Successful Response'}, '422': {'content': {...}, 'description': 'Validation Error'}}, ...}}, ...}}

    def test_schemas_have_examples(openapi_spec):
        """Key schemas should have examples defined."""
        schemas = openapi_spec.get("components", {}).get("schemas", {})
    
        key_schemas = ["ErrorEnvelope", "HealthResponse", "AppInfoResponse"]
    
        for schema_name in key_schemas:
            if schema_name in schemas:
                schema = schemas[schema_name]
>               assert "example" in schema or "examples" in schema or "jsonSchema" in schema.get("example", {}), (
                    f"Schema {schema_name} should have example metadata"
                )
E               AssertionError: Schema HealthResponse should have example metadata
E               assert ('example' in {'description': 'Health check response.', 'properties': {'status': {'description': 'Service status', 'title': 'Status', 'type': 'string'}, 'timestamp': {'format': 'date-time', 'title': 'Timestamp', 'type': 'string'}, 'version': {'description': 'API version', 'title': 'Version', 'type': 'string'}}, 'required': ['status', 'version'], 'title': 'HealthResponse', ...} or 'examples' in {'description': 'Health check response.', 'properties': {'status': {'description': 'Service status', 'title': 'Status', 'type': 'string'}, 'timestamp': {'format': 'date-time', 'title': 'Timestamp', 'type': 'string'}, 'version': {'description': 'API version', 'title': 'Version', 'type': 'string'}}, 'required': ['status', 'version'], 'title': 'HealthResponse', ...} or 'jsonSchema' in {})
E                +  where {} = <built-in method get of dict object at 0x7474b3bcf500>('example', {})
E                +    where <built-in method get of dict object at 0x7474b3bcf500> = {'description': 'Health check response.', 'properties': {'status': {'description': 'Service status', 'title': 'Status', 'type': 'string'}, 'timestamp': {'format': 'date-time', 'title': 'Timestamp', 'type': 'string'}, 'version': {'description': 'API version', 'title': 'Version', 'type': 'string'}}, 'required': ['status', 'version'], 'title': 'HealthResponse', ...}.get

tests/unit/test_openapi_contract.py:166: AssertionError
------------------------------------------------------------ Captured stdout setup -------------------------------------------------------------
2026-05-19T10:35:25.263540Z [info     ] http_request_started           [app.middleware.logging] client_host=testclient content_length=None content_type=None method=GET path=/openapi.json query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=b5686881-4173-4d user_agent=testclient
2026-05-19T10:35:25.268421Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=4.68 memory={'rss_mb': 190.4, 'vms_mb': 859.35} method=GET path=/openapi.json response_content_length=149458 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=b5686881-4173-4d
HTTP Request: GET http://testserver/openapi.json "HTTP/1.1 200 OK"
-------------------------------------------------------------- Captured log setup --------------------------------------------------------------
INFO     app.middleware.logging:logging.py:49 2026-05-19T10:35:25.263540Z [info     ] http_request_started           [app.middleware.logging] client_host=testclient content_length=None content_type=None method=GET path=/openapi.json query= service='Dashboard Analytics API' service_version=1.0.0 trace_id=b5686881-4173-4d user_agent=testclient
INFO     app.middleware.logging:logging.py:81 2026-05-19T10:35:25.268421Z [info     ] http_request_completed         [app.middleware.logging] elapsed_ms=4.68 memory={'rss_mb': 190.4, 'vms_mb': 859.35} method=GET path=/openapi.json response_content_length=149458 response_content_type=application/json service='Dashboard Analytics API' service_version=1.0.0 status_code=200 trace_id=b5686881-4173-4d
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/openapi.json "HTTP/1.1 200 OK"
=============================================================== warnings summary ===============================================================
app/config.py:8
  /home/ivan/projects/DiplomaAPI/app/config.py:8: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class Settings(BaseSettings):

app/schemas/common.py:29
  /home/ivan/projects/DiplomaAPI/app/schemas/common.py:29: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class PaginatedResponse(BaseModel, Generic[T]):

app/schemas/kpi.py:21
  /home/ivan/projects/DiplomaAPI/app/schemas/kpi.py:21: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class KPICurrentResponse(BaseModel):

app/schemas/kpi.py:43
  /home/ivan/projects/DiplomaAPI/app/schemas/kpi.py:43: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class KPIHistoryResponse(BaseModel):

app/schemas/kpi.py:64
  /home/ivan/projects/DiplomaAPI/app/schemas/kpi.py:64: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class KPICompareResponse(BaseModel):

app/schemas/sales.py:21
  /home/ivan/projects/DiplomaAPI/app/schemas/sales.py:21: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class SalesSummaryResponse(BaseModel):

app/schemas/sales.py:42
  /home/ivan/projects/DiplomaAPI/app/schemas/sales.py:42: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class SalesTrendsResponse(BaseModel):

app/schemas/sales.py:64
  /home/ivan/projects/DiplomaAPI/app/schemas/sales.py:64: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class TopProductsResponse(BaseModel):

app/schemas/sales.py:84
  /home/ivan/projects/DiplomaAPI/app/schemas/sales.py:84: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class SalesRegionsResponse(BaseModel):

app/schemas/orders.py:19
  /home/ivan/projects/DiplomaAPI/app/schemas/orders.py:19: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class OrderStatusSummaryResponse(BaseModel):

app/schemas/orders.py:32
  /home/ivan/projects/DiplomaAPI/app/schemas/orders.py:32: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class OrderListItem(BaseModel):

app/schemas/orders.py:54
  /home/ivan/projects/DiplomaAPI/app/schemas/orders.py:54: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class OrderListResponse(BaseModel):

app/schemas/orders.py:76
  /home/ivan/projects/DiplomaAPI/app/schemas/orders.py:76: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class OrderDetailResponse(BaseModel):

app/schemas/orders.py:97
  /home/ivan/projects/DiplomaAPI/app/schemas/orders.py:97: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class PlanExecutionLineItem(BaseModel):

app/schemas/orders.py:111
  /home/ivan/projects/DiplomaAPI/app/schemas/orders.py:111: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class PlanExecutionResponse(BaseModel):

app/schemas/orders.py:120
  /home/ivan/projects/DiplomaAPI/app/schemas/orders.py:120: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class DowntimeLineItem(BaseModel):

app/schemas/orders.py:132
  /home/ivan/projects/DiplomaAPI/app/schemas/orders.py:132: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class DowntimeResponse(BaseModel):

app/schemas/quality.py:17
  /home/ivan/projects/DiplomaAPI/app/schemas/quality.py:17: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class QualitySummaryResponse(BaseModel):

app/schemas/quality.py:42
  /home/ivan/projects/DiplomaAPI/app/schemas/quality.py:42: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class DefectTrendsResponse(BaseModel):

app/schemas/quality.py:52
  /home/ivan/projects/DiplomaAPI/app/schemas/quality.py:52: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class QualityLotItem(BaseModel):

app/schemas/quality.py:66
  /home/ivan/projects/DiplomaAPI/app/schemas/quality.py:66: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class QualityLotsResponse(BaseModel):

app/schemas/quality.py:80
  /home/ivan/projects/DiplomaAPI/app/schemas/quality.py:80: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class LotDeviationItem(BaseModel):

app/schemas/quality.py:91
  /home/ivan/projects/DiplomaAPI/app/schemas/quality.py:91: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class LotDeviationsResponse(BaseModel):

app/schemas/sync.py:22
  /home/ivan/projects/DiplomaAPI/app/schemas/sync.py:22: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class SyncStatusResponse(BaseModel):

app/schemas/sync.py:32
  /home/ivan/projects/DiplomaAPI/app/schemas/sync.py:32: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class SyncTriggerResponse(BaseModel):

app/schemas/analytics.py:21
  /home/ivan/projects/DiplomaAPI/app/schemas/analytics.py:21: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class BatchInputResponse(BaseModel):

app/schemas/analytics.py:68
  /home/ivan/projects/DiplomaAPI/app/schemas/analytics.py:68: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class DowntimeEventResponse(BaseModel):

app/schemas/analytics.py:118
  /home/ivan/projects/DiplomaAPI/app/schemas/analytics.py:118: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class PromoCampaignResponse(BaseModel):

app/schemas/gateway_responses.py:16
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:16: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class LoginResponse(BaseModel):

app/schemas/gateway_responses.py:34
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:34: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class LocationItem(BaseModel):

app/schemas/gateway_responses.py:64
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:64: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class DepartmentItem(BaseModel):

app/schemas/gateway_responses.py:96
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:96: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class PositionItem(BaseModel):

app/schemas/gateway_responses.py:121
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:121: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class EmployeeItem(BaseModel):

app/schemas/gateway_responses.py:162
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:162: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class WorkstationItem(BaseModel):

app/schemas/gateway_responses.py:196
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:196: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class ProductionLineItem(BaseModel):

app/schemas/gateway_responses.py:233
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:233: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class ProductItem(BaseModel):

app/schemas/gateway_responses.py:269
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:269: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class OrderItem(BaseModel):

app/schemas/gateway_responses.py:307
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:307: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class OutputItem(BaseModel):

app/schemas/gateway_responses.py:356
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:356: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class SaleItem(BaseModel):

app/schemas/gateway_responses.py:392
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:392: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class SalesSummaryItem(BaseModel):

app/schemas/gateway_responses.py:420
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:420: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class KpiResponse(BaseModel):

app/schemas/gateway_responses.py:440
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:440: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class QualityResultItem(BaseModel):

app/schemas/gateway_responses.py:472
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:472: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class SensorParameterEmbedded(BaseModel):

app/schemas/gateway_responses.py:488
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:488: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class SensorReadingItem(BaseModel):

app/schemas/gateway_responses.py:526
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:526: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class InventoryItem(BaseModel):

app/schemas/gateway_responses.py:554
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:554: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class UnitOfMeasureItem(BaseModel):

app/schemas/gateway_responses.py:578
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:578: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class CustomerItem(BaseModel):

app/schemas/gateway_responses.py:600
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:600: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class WarehouseItem(BaseModel):

app/schemas/gateway_responses.py:628
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:628: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class BatchInputItem(BaseModel):

app/schemas/gateway_responses.py:656
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:656: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class DowntimeEventItem(BaseModel):

app/schemas/gateway_responses.py:688
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:688: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class OtifResponse(BaseModel):

app/schemas/gateway_responses.py:708
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:708: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class QualitySpecItem(BaseModel):

app/schemas/gateway_responses.py:736
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:736: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class SensorParameterItem(BaseModel):

app/schemas/gateway_responses.py:760
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:760: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class ShiftTemplateItem(BaseModel):

app/schemas/gateway_responses.py:788
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:788: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class PromoCampaignItem(BaseModel):

app/schemas/gateway_responses.py:820
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:820: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class PostalAreaItem(BaseModel):

app/schemas/gateway_responses.py:846
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:846: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class ProductionLineViewItem(BaseModel):

app/schemas/gateway_responses.py:876
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:876: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class CurrentUserResponse(BaseModel):

app/schemas/gateway_responses.py:898
  /home/ivan/projects/DiplomaAPI/app/schemas/gateway_responses.py:898: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class KpiBreakdownItem(BaseModel):

tests/integration/test_finance_dashboard_routes.py: 96 warnings
tests/integration/test_gm_dashboard_routes.py: 32 warnings
tests/integration/test_orders_routes.py: 90 warnings
tests/integration/test_output_routes.py: 56 warnings
tests/integration/test_phase2_3_kpi_routes.py: 6 warnings
tests/integration/test_phase4_cursor_pagination_routes.py: 16 warnings
tests/integration/test_production_lines_routes.py: 42 warnings
tests/integration/test_qe_dashboard_routes.py: 100 warnings
tests/integration/test_quality_routes.py: 154 warnings
tests/integration/test_sales_routes.py: 90 warnings
tests/integration/test_sensor_sync.py: 621 warnings
tests/integration/test_sensors_routes.py: 242 warnings
tests/unit/test_finance_dashboard_service.py: 120 warnings
tests/unit/test_gm_dashboard_service.py: 64 warnings
tests/unit/test_line_master_dashboard_service.py: 180 warnings
tests/unit/test_qe_dashboard_service.py: 232 warnings
tests/unit/test_sales_service.py: 286 warnings
  /home/ivan/projects/DiplomaAPI/.venv/lib/python3.12/site-packages/sqlalchemy/sql/schema.py:3624: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore

tests/integration/test_sensor_sync.py::test_sync_sensors_creates_full_hierarchy
tests/integration/test_sensor_sync.py::test_sync_sensors_updates_existing_sensor
tests/integration/test_sensor_sync.py::test_sync_sensors_batches_multiple_readings
  /home/ivan/projects/DiplomaAPI/app/services/sensor_service.py:284: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    snapshot_date = datetime.utcnow()

tests/unit/test_gateway_client.py::test_gateway_client_request_includes_bearer_auth
  /home/ivan/projects/DiplomaAPI/app/services/gateway_client.py:228: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
    log_data_flow(
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

tests/unit/test_gateway_client.py::test_gateway_client_request_includes_bearer_auth
  /home/ivan/projects/DiplomaAPI/app/services/gateway_client.py:238: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
    logger.info(
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

tests/unit/test_gateway_client.py::test_gateway_client_request_includes_bearer_auth
  /usr/lib/python3.12/asyncio/events.py:88: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
    self._context.run(self._callback, *self._args)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

tests/unit/test_gateway_client.py::test_gateway_client_request_handles_server_error
  /home/ivan/projects/DiplomaAPI/app/services/gateway_client.py:251: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
    response.raise_for_status()
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================================================== short test summary info ============================================================
FAILED tests/integration/test_personnel_routes.py::test_empty_tables_return_empty_lists - assert 404 == 200
FAILED tests/integration/test_personnel_routes.py::test_unknown_filter_type_returns_empty - assert 404 == 200
FAILED tests/integration/test_phase2_3_kpi_routes.py::test_get_line_productivity_endpoint - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
FAILED tests/integration/test_phase2_3_kpi_routes.py::test_set_kpi_config_endpoint - assert 404 == 201
FAILED tests/integration/test_phase2_3_kpi_routes.py::test_get_kpi_config_endpoint - assert 404 == 200
FAILED tests/integration/test_phase4_cursor_pagination_routes.py::test_batch_inputs_cursor_pagination - KeyError: 'has_more'
FAILED tests/integration/test_phase4_cursor_pagination_routes.py::test_batch_inputs_invalid_cursor_returns_400 - assert 200 == 400
FAILED tests/integration/test_phase4_cursor_pagination_routes.py::test_downtime_events_cursor_pagination - KeyError: 'has_more'
FAILED tests/integration/test_phase4_cursor_pagination_routes.py::test_downtime_events_invalid_cursor_returns_400 - assert 200 == 400
FAILED tests/integration/test_production_analytics_include_routes.py::test_get_kpi_breakdown_include_production_line - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
FAILED tests/integration/test_production_lines_routes.py::test_list_production_lines_division_filter - assert 2 == 1
FAILED tests/integration/test_production_lines_routes.py::test_list_production_lines_total_scoped_to_filter - assert 2 == 1
FAILED tests/integration/test_sensor_sync.py::test_sync_sensors_creates_full_hierarchy - assert None is not None
FAILED tests/integration/test_sensor_sync.py::test_sync_sensors_skips_missing_sensor_id - pydantic_core._pydantic_core.ValidationError: 1 validation error for SensorReadingItem
FAILED tests/integration/test_sensor_sync.py::test_sync_sensors_batches_multiple_readings - AttributeError: 'AsyncSession' object has no attribute 'query'
FAILED tests/integration/test_sensor_sync.py::test_sync_sensors_handles_missing_parameter - pydantic_core._pydantic_core.ValidationError: 1 validation error for SensorReadingItem
FAILED tests/integration/test_sensors_routes.py::test_sensor_history_filter_by_parameter - assert 0 == 3
FAILED tests/integration/test_sensors_routes.py::test_sensor_alerts_only_bad_quality - assert 0 == 2
FAILED tests/integration/test_sensors_routes.py::test_sensor_stats_alert_count - assert 0 == 2
FAILED tests/unit/test_kpi_service.py::test_compare_kpi_defect_rate_change_calculation - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
FAILED tests/unit/test_kpi_service.py::test_compare_kpi_order_completion_change_calculation - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
FAILED tests/unit/test_kpi_service.py::test_compare_kpi_with_zero_total_orders - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
FAILED tests/unit/test_openapi_contract.py::test_root_endpoint_has_response_model - AssertionError: Root endpoint must have response_model (schema ref)
FAILED tests/unit/test_openapi_contract.py::test_inventory_trends_has_response_model - AssertionError: Inventory trends must have response_model
FAILED tests/unit/test_openapi_contract.py::test_sensors_stats_has_response_model - AssertionError: Sensors stats must have response_model
FAILED tests/unit/test_openapi_contract.py::test_all_endpoints_have_response_models - AssertionError: Endpoints without response_model: ['/', '/api/v1/sync/running', '/api/v1/products', '/api/v1/products/{product_id}', '/api/...
FAILED tests/unit/test_openapi_contract.py::test_schemas_have_examples - AssertionError: Schema HealthResponse should have example metadata
ERROR tests/integration/test_gm_dashboard_routes.py::test_oee_summary_returns_200 - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/integration/test_gm_dashboard_routes.py::test_oee_summary_default_period_days - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/integration/test_inventory_routes.py::test_inventory_current_success - TypeError: 'location' is an invalid keyword argument for Warehouse
ERROR tests/integration/test_inventory_routes.py::test_inventory_current_returns_latest_only - TypeError: 'location' is an invalid keyword argument for Warehouse
ERROR tests/integration/test_inventory_routes.py::test_inventory_current_filter_by_warehouse - TypeError: 'location' is an invalid keyword argument for Warehouse
ERROR tests/integration/test_inventory_routes.py::test_inventory_current_filter_by_product - TypeError: 'location' is an invalid keyword argument for Warehouse
ERROR tests/integration/test_inventory_routes.py::test_inventory_current_item_fields - TypeError: 'location' is an invalid keyword argument for Warehouse
ERROR tests/integration/test_inventory_routes.py::test_inventory_trends_success - TypeError: 'location' is an invalid keyword argument for Warehouse
ERROR tests/integration/test_personnel_routes.py::test_get_departments_returns_200
ERROR tests/integration/test_personnel_routes.py::test_get_departments_filter_by_type
ERROR tests/integration/test_personnel_routes.py::test_get_positions_returns_200
ERROR tests/integration/test_personnel_routes.py::test_get_employees_returns_200
ERROR tests/integration/test_personnel_routes.py::test_get_locations_returns_200
ERROR tests/integration/test_personnel_routes.py::test_get_summary_returns_counts
ERROR tests/integration/test_products_routes.py::test_products_list_include_inventory_summary - TypeError: 'location' is an invalid keyword argument for Warehouse
ERROR tests/integration/test_products_routes.py::test_product_detail_include_inventory_summary - TypeError: 'location' is an invalid keyword argument for Warehouse
ERROR tests/unit/test_gm_dashboard_service.py::test_get_oee_summary_returns_all_lines - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_gm_dashboard_service.py::test_get_oee_summary_ranked_best_first - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_gm_dashboard_service.py::test_get_oee_summary_vs_target_correct - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_gm_dashboard_service.py::test_get_oee_summary_trend_has_data_points - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_gm_dashboard_service.py::test_get_oee_summary_filters_by_period - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_kpi_service.py::test_get_current_kpi_returns_most_recent - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_kpi_service.py::test_get_current_kpi_with_production_line_filter - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_kpi_service.py::test_get_kpi_history_returns_ordered_by_date - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_kpi_service.py::test_get_kpi_history_with_date_filtering - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_kpi_service.py::test_get_all_kpi_returns_all_records - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_kpi_service.py::test_get_all_kpi_ordered_by_period - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_kpi_service.py::test_get_all_kpi_with_production_line_filter - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_kpi_service.py::test_compare_kpi_periods_calculates_output_change - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_kpi_service.py::test_compare_kpi_periods_with_missing_period - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_oee_service.py::test_calculate_availability_with_downtime - pytest.PytestRemovedIn9Warning: 'test_calculate_availability_with_downtime' requested an async fixture 'sample_production_line', with no pl...
ERROR tests/unit/test_oee_service.py::test_calculate_performance - pytest.PytestRemovedIn9Warning: 'test_calculate_performance' requested an async fixture 'sample_production_line', with no plugin or hook th...
ERROR tests/unit/test_oee_service.py::test_calculate_quality_with_accepted - pytest.PytestRemovedIn9Warning: 'test_calculate_quality_with_accepted' requested an async fixture 'sample_production_line', with no plugin ...
ERROR tests/unit/test_oee_service.py::test_calculate_oee_for_line - pytest.PytestRemovedIn9Warning: 'test_calculate_oee_for_line' requested an async fixture 'sample_production_line', with no plugin or hook t...
ERROR tests/unit/test_oee_service.py::test_calculate_oee_summary - pytest.PytestRemovedIn9Warning: 'test_calculate_oee_summary' requested an async fixture 'sample_production_line', with no plugin or hook th...
ERROR tests/unit/test_oee_service.py::test_set_capacity_plan - pytest.PytestRemovedIn9Warning: 'test_set_capacity_plan' requested an async fixture 'sample_production_line', with no plugin or hook that h...
ERROR tests/unit/test_production_analytics_kpi.py::test_get_line_productivity_returns_list - pytest.PytestRemovedIn9Warning: 'test_get_line_productivity_returns_list' requested an async fixture 'kpi_service', with no plugin or hook ...
ERROR tests/unit/test_production_analytics_kpi.py::test_get_line_productivity_calculates_correctly - pytest.PytestRemovedIn9Warning: 'test_get_line_productivity_calculates_correctly' requested an async fixture 'kpi_service', with no plugin ...
ERROR tests/unit/test_production_analytics_kpi.py::test_get_scrap_percentage_returns_correct_structure - pytest.PytestRemovedIn9Warning: 'test_get_scrap_percentage_returns_correct_structure' requested an async fixture 'kpi_service', with no plu...
ERROR tests/unit/test_production_analytics_kpi.py::test_get_scrap_percentage_calculates_correctly - pytest.PytestRemovedIn9Warning: 'test_get_scrap_percentage_calculates_correctly' requested an async fixture 'kpi_service', with no plugin o...
ERROR tests/unit/test_sales_service.py::test_get_sales_trends_returns_ordered_by_date - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_sales_service.py::test_get_sales_trends_with_region_filter - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_sales_service.py::test_get_sales_trends_with_channel_filter - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
ERROR tests/unit/test_sales_service.py::test_aggregate_from_raw_returns_list - TypeError: 'production_line' is an invalid keyword argument for AggregatedKPI
===================================== 27 failed, 157 passed, 2493 warnings, 44 errors in 306.41s (0:05:06)