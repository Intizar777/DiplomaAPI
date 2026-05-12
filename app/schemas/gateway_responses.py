"""
Pydantic models for validating Gateway API responses.
Source of truth: docs/gateway-api-responses.md
"""

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================================================
# Auth Responses
# ============================================================================

class LoginResponse(BaseModel):
    """Response from POST /auth/login"""
    accessToken: str
    refreshToken: str

    class Config:
        json_schema_extra = {
            "example": {
                "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refreshToken": "NOw4NwxQ36oTDVysxg6EghmAHHFHARCaMPVbeaD6_QQ"
            }
        }


# ============================================================================
# Personnel Models
# ============================================================================

class LocationItem(BaseModel):
    """Single location from /personnel/locations"""
    id: UUID
    name: str
    code: str
    type: str
    streetAddress: str
    postalAreaId: UUID
    sourceSystemId: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "c9b5f796-b67f-4790-966c-b7d6225c4d30",
                "name": "Жировой комбинат (ЕЖК) - Майонезы",
                "code": "EKB_PLANT",
                "type": "factory",
                "streetAddress": "ул. Титова, 27",
                "postalAreaId": "549cb1e5-77f6-4318-a874-64afaa66f313",
                "sourceSystemId": None
            }
        }


class LocationsResponse(BaseModel):
    """Response from GET /personnel/locations"""
    locations: List[LocationItem]
    total: int


class DepartmentItem(BaseModel):
    """Single department from /personnel/departments"""
    id: UUID
    name: str
    code: str
    type: str
    locationId: Optional[UUID] = None
    parentId: Optional[UUID] = None
    headEmployeeId: Optional[UUID] = None
    sourceSystemId: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ff4d3613-be20-4931-8871-3529f77746a2",
                "name": "IT-отдел",
                "code": "DEP-UPR-ITD",
                "type": "department",
                "locationId": "c9b5f796-b67f-4790-966c-b7d6225c4d30",
                "parentId": "f22958aa-3cb7-4ed2-a122-60f1569c473e",
                "headEmployeeId": "58156fda-4575-4271-b165-797b2549714c",
                "sourceSystemId": None
            }
        }


class DepartmentsResponse(BaseModel):
    """Response from GET /personnel/departments"""
    departments: List[DepartmentItem]
    total: int


class PositionItem(BaseModel):
    """Single position from /personnel/positions"""
    id: UUID
    name: str = Field(alias="title")
    code: str
    departmentId: Optional[UUID] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "27cde08e-dafe-40b0-a6b9-1f0ad9401400",
                "title": "HR-менеджер",
                "code": "POS-0250",
                "departmentId": "ab751713-a58e-4f2e-b73e-02e9986f5aa8"
            }
        }
        populate_by_name = True


class PositionsResponse(BaseModel):
    """Response from GET /personnel/positions"""
    positions: List[PositionItem]
    total: int


class EmployeeItem(BaseModel):
    """Single employee from /personnel/employees"""
    id: UUID
    employeeNumber: str = Field(alias="personnelNumber")
    fullName: str
    dateOfBirth: datetime
    positionId: UUID
    departmentId: UUID
    workstationId: Optional[UUID] = None
    hireDate: datetime
    terminationDate: Optional[datetime] = None
    employmentType: str
    status: str
    sourceSystemId: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "623e2a46-0c46-4062-8709-b0e07d8a9060",
                "personnelNumber": "EMP-00244",
                "fullName": "Абрамова Анастасия Романовна",
                "dateOfBirth": "1975-11-24T00:00:00.000Z",
                "positionId": "23f581ec-b18b-468d-9710-81fceb35fe8a",
                "departmentId": "ab751713-a58e-4f2e-b73e-02e9986f5aa8",
                "workstationId": "14c6beeb-9efa-47ea-986b-99ed9909d966",
                "hireDate": "2024-01-18T00:00:00.000Z",
                "terminationDate": None,
                "employmentType": "main",
                "status": "active",
                "sourceSystemId": None
            }
        }
        populate_by_name = True


class EmployeesResponse(BaseModel):
    """Response from GET /personnel/employees"""
    employees: List[EmployeeItem]
    total: int


class WorkstationItem(BaseModel):
    """Single workstation from /personnel/workstations"""
    id: UUID
    name: str
    code: str
    locationId: UUID
    productionLineId: Optional[UUID] = None
    workstationType: str
    sourceSystemId: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "dd6dbbcd-3bd2-4bfa-9dd9-a54550a8a820",
                "name": "Контрольный пост - Завод ТЗПМ",
                "code": "TAM_CTRL1",
                "locationId": "0cc70402-a232-4209-924c-98f46ec5a6d1",
                "productionLineId": "4d1b5527-2315-0129-4000-409c8f901120",
                "workstationType": "control_point",
                "sourceSystemId": None
            }
        }


class WorkstationsResponse(BaseModel):
    """Response from GET /personnel/workstations"""
    workstations: List[WorkstationItem]
    total: int


# ============================================================================
# Production Models
# ============================================================================

class ProductionLineItem(BaseModel):
    """Single production line from /production/production-lines"""
    id: UUID
    name: str
    code: str
    description: str
    isActive: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "3d57ea5f-fcd5-3a77-24cb-7996f830f190",
                "name": "Линия А - Основное производство (Алматы)",
                "code": "ALM_LINE_A",
                "description": "Линия А - Основное производство (Алматы)",
                "isActive": True,
                "createdAt": "2026-05-08T15:05:59.117Z",
                "updatedAt": "2026-05-08T15:05:59.117Z"
            }
        }


class ProductionLinesResponse(BaseModel):
    """Response from GET /production/production-lines"""
    productionLines: List[ProductionLineItem]
    total: int


class UnitOfMeasure(BaseModel):
    """Unit of measure nested object"""
    id: UUID
    code: str
    name: str


class ProductItem(BaseModel):
    """Single product from /production/products"""
    id: UUID
    code: str
    name: str
    category: str
    brand: Optional[str] = None
    unitOfMeasure: Optional[UnitOfMeasure] = None
    shelfLifeDays: Optional[int] = None
    requiresQualityCheck: bool

    class Config:
        json_schema_extra = {
            "example": {
                "id": "d9ef7951-3e45-4c96-a01d-7c92286c0213",
                "code": "PKG-BOTTLE-500ML",
                "name": "Бутылка ПЭТ 500мл",
                "category": "packaging",
                "brand": None,
                "unitOfMeasure": {
                    "id": "5cbeb66e-4a7b-4e46-bc43-83308c6ae766",
                    "code": "шт",
                    "name": "шт"
                },
                "shelfLifeDays": None,
                "requiresQualityCheck": False
            }
        }


class ProductsResponse(BaseModel):
    """Response from GET /production/products"""
    products: List[ProductItem]
    total: int


class OrderItem(BaseModel):
    """Single order from /production/orders"""
    id: UUID
    externalOrderId: str
    productId: UUID
    targetQuantity: float
    actualQuantity: float
    status: str
    productionLineId: UUID
    plannedStart: datetime
    plannedEnd: datetime
    actualStart: Optional[datetime] = None
    actualEnd: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "0d341281-2caf-4d43-ae64-0387c2cdfe85",
                "externalOrderId": "ORD-004802",
                "productId": "d8128e57-29d0-48e8-9d51-5a35b387262f",
                "targetQuantity": 6543.971,
                "actualQuantity": 6521.551,
                "status": "completed",
                "productionLineId": "a0a65c5f-bb95-e4a8-e1be-3b6dff660b2d",
                "plannedStart": "2026-05-04T20:48:11.091Z",
                "plannedEnd": "2026-05-06T20:48:11.091Z",
                "actualStart": "2026-05-05T20:48:11.091Z",
                "actualEnd": "2026-05-05T20:48:11.091Z"
            }
        }


class OrdersResponse(BaseModel):
    """Response from GET /production/orders"""
    orders: List[OrderItem]
    total: int


class OutputItem(BaseModel):
    """Single output from /production/output"""
    id: UUID
    orderId: UUID
    productId: UUID
    lotNumber: str
    quantity: float
    qualityStatus: str
    productionDate: datetime
    shift: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a4e2b4f1-b90d-45f6-87bd-411e7d2a6483",
                "orderId": "0d341281-2caf-4d43-ae64-0387c2cdfe85",
                "productId": "d8128e57-29d0-48e8-9d51-5a35b387262f",
                "lotNumber": "LOT-20260508-905",
                "quantity": 854.363,
                "qualityStatus": "approved",
                "productionDate": "2026-05-08T20:48:11.091Z",
                "shift": "Утренняя"
            }
        }


class OutputsResponse(BaseModel):
    """Response from GET /production/output"""
    outputs: List[OutputItem]
    total: int


class OrderDetailItem(BaseModel):
    """Output item nested in order detail"""
    id: UUID
    orderId: UUID
    productId: UUID
    lotNumber: str
    quantity: float
    qualityStatus: str
    productionDate: datetime
    shift: str


class OrderDetailResponse(OrderItem):
    """Response from GET /production/orders/{id} - order with outputs"""
    outputs: List[OrderDetailItem]


class SaleItem(BaseModel):
    """Single sale from /production/sales"""
    id: UUID
    externalId: str
    productId: UUID
    customerId: UUID
    quantity: float
    amount: float
    cost: float = None
    saleDate: datetime
    region: str
    channel: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "b9647330-2d05-422b-a77d-2791994f11c3",
                "externalId": "SALE-0049852",
                "productId": "a31b5c69-4095-4e12-869c-b8b459d58f8f",
                "customerId": "7fbf1f89-f3b7-463c-9c8f-fdf628c23195",
                "quantity": 1501.444,
                "amount": 1728026.56,
                "cost": 1123216.86,
                "saleDate": "2026-05-04T00:00:00.000Z",
                "region": "ПФО",
                "channel": "retail"
            }
        }


class SalesResponse(BaseModel):
    """Response from GET /production/sales"""
    sales: List[SaleItem]
    total: int


class SalesSummaryItem(BaseModel):
    """Single group in sales summary"""
    groupKey: str
    totalQuantity: float
    totalAmount: float
    salesCount: int

    class Config:
        json_schema_extra = {
            "example": {
                "groupKey": "СФО",
                "totalQuantity": 20993378.776,
                "totalAmount": 7834257524.91,
                "salesCount": 5157
            }
        }


class SalesSummaryResponse(BaseModel):
    """Response from GET /production/sales/summary"""
    summary: List[SalesSummaryItem]
    totalAmount: float
    totalQuantity: float
    total: int


class KpiResponse(BaseModel):
    """Response from GET /production/kpi"""
    totalOutput: float
    defectRate: float
    completedOrders: int
    totalOrders: int
    oeeEstimate: float

    class Config:
        json_schema_extra = {
            "example": {
                "totalOutput": 79190291.608,
                "defectRate": 0.03487299201612002,
                "completedOrders": 3910,
                "totalOrders": 5000,
                "oeeEstimate": 0.7547293202433941
            }
        }


class QualityResultItem(BaseModel):
    """Single quality result from /production/quality"""
    id: UUID
    lotNumber: str
    qualitySpecId: UUID
    productId: str = ""
    parameterName: str = ""
    resultValue: float
    qualityStatus: str
    testDate: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "2c685d39-8402-421d-b731-7c7155d981b3",
                "lotNumber": "LOT-20260508-905",
                "qualitySpecId": "abd133b5-426d-4c40-bc31-a249f8dbb09c",
                "productId": "",
                "parameterName": "",
                "resultValue": 0.650719,
                "qualityStatus": "approved",
                "testDate": "2026-05-09T20:48:11.091Z"
            }
        }


class QualityResponse(BaseModel):
    """Response from GET /production/quality"""
    results: List[QualityResultItem]
    total: int


class SensorParameterEmbedded(BaseModel):
    """Embedded sensor parameter from /production/sensors with include=sensorParameter"""
    id: UUID
    name: str
    unit: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "6b0ea8f9-168b-406e-8015-879fd71016fc",
                "name": "Расход жидкости",
                "unit": "л/ч"
            }
        }


class SensorReadingItem(BaseModel):
    """Single sensor reading from /production/sensors"""
    id: UUID
    sensorId: UUID
    deviceId: str
    productionLineId: UUID
    sensorParameterId: UUID
    value: float
    quality: str
    recordedAt: datetime
    sensorParameter: Optional[SensorParameterEmbedded] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "6f62c3b3-9102-43a9-befa-c017328ce66c",
                "sensorId": "46e965ef-efa5-4839-8dec-1974596faf46",
                "deviceId": "SENSOR-NOG_LINE_A-T03-РАСХ",
                "productionLineId": "a0a65c5f-bb95-e4a8-e1be-3b6dff660b2d",
                "sensorParameterId": "6b0ea8f9-168b-406e-8015-879fd71016fc",
                "value": 4360.7101,
                "quality": "bad",
                "recordedAt": "2026-05-05T12:59:00.000Z",
                "sensorParameter": {
                    "id": "6b0ea8f9-168b-406e-8015-879fd71016fc",
                    "name": "Расход жидкости",
                    "unit": "л/ч"
                }
            }
        }


class SensorReadingsResponse(BaseModel):
    """Response from GET /production/sensors"""
    readings: List[SensorReadingItem]
    total: int


class InventoryItem(BaseModel):
    """Single inventory item from /production/inventory"""
    id: UUID
    productId: UUID
    warehouseId: UUID
    lotNumber: str
    quantity: float
    lastUpdated: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "c3d7a566-5bb8-4ac1-9774-e6542c12c1a5",
                "productId": "cef90bf6-801f-48b4-9bbe-2edb9668c824",
                "warehouseId": "0f0ece7c-b002-444c-b9c8-61bf8be0f64e",
                "lotNumber": "LOT-20260314-004",
                "quantity": 2352.971,
                "lastUpdated": "2026-03-14T03:41:10.369Z"
            }
        }


class InventoryResponse(BaseModel):
    """Response from GET /production/inventory"""
    inventory: List[InventoryItem]
    total: int


class UnitOfMeasureItem(BaseModel):
    """Single unit of measure from /production/units-of-measure"""
    id: UUID
    code: str
    name: str
    createdAt: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "bfff1635-3800-4fb8-8e66-e7ed300691e0",
                "code": "кг",
                "name": "кг",
                "createdAt": "2026-05-08T15:05:57.765Z"
            }
        }


class UnitsOfMeasureResponse(BaseModel):
    """Response from GET /production/units-of-measure"""
    unitsOfMeasure: List[UnitOfMeasureItem]
    total: int


class CustomerItem(BaseModel):
    """Single customer from /production/customers"""
    id: UUID
    name: str
    createdAt: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ec3464dc-777b-485a-adba-5d99408d23c1",
                "name": "ООО Монетка",
                "createdAt": "2026-05-08T15:06:00.413Z"
            }
        }


class CustomersResponse(BaseModel):
    """Response from GET /production/customers"""
    customers: List[CustomerItem]
    total: int


class WarehouseItem(BaseModel):
    """Single warehouse from /production/warehouses"""
    id: UUID
    name: str
    code: str
    createdAt: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "36688e3d-5f73-4327-bdd5-c0148bf901f6",
                "name": "Архивный склад",
                "code": "WH-ARCH-01",
                "createdAt": "2026-05-08T15:05:59.874Z"
            }
        }


class WarehousesResponse(BaseModel):
    """Response from GET /production/warehouses"""
    warehouses: List[WarehouseItem]
    total: int
