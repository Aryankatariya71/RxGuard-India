"""SQLAlchemy ORM models — Stage 1 schema for RxGuard India."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    standard_identifier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    synonyms: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="REVIEW_PENDING")
    source: Mapped[str | None] = mapped_column(String(512), nullable=True)
    dataset_version: Mapped[str] = mapped_column(String(64), default="demo-1.0")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    products = relationship("ProductIngredient", back_populates="ingredient")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (Index("ix_products_normalized_name", "normalized_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    strength_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dosage_form: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    route: Mapped[str | None] = mapped_column(String(64), nullable=True)
    identity_status: Mapped[str] = mapped_column(String(64), default="UNRESOLVED")
    source: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_discontinued: Mapped[bool] = mapped_column(Boolean, default=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    ingredients = relationship("ProductIngredient", back_populates="product")


# Backward-compatible alias used by earlier HM-02 services during migration
MedicineProduct = Product


class ProductIngredient(Base):
    __tablename__ = "product_ingredients"
    __table_args__ = (UniqueConstraint("product_id", "ingredient_id", name="uq_product_ing"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False)
    ingredient_id: Mapped[str] = mapped_column(ForeignKey("ingredients.id"), nullable=False)
    strength_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    strength_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    per_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    per_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quantity_basis: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active_flag: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str | None] = mapped_column(String(512), nullable=True)
    incomplete_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    product = relationship("Product", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="products")

    # HM-02 compatibility accessors
    @property
    def ingredient_strength(self) -> float | None:
        return self.strength_value


class InteractionRule(Base):
    __tablename__ = "interaction_rules"
    __table_args__ = (
        UniqueConstraint("ingredient_a_id", "ingredient_b_id", "rule_code", name="uq_int_pair_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    rule_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    ingredient_a_id: Mapped[str] = mapped_column(ForeignKey("ingredients.id"), nullable=False)
    ingredient_b_id: Mapped[str] = mapped_column(ForeignKey("ingredients.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="drug_drug")
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_source: Mapped[str | None] = mapped_column(String(512), nullable=True)
    evidence_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    version: Mapped[str] = mapped_column(String(64), default="demo-1.0")
    status: Mapped[str] = mapped_column(String(64), default="REVIEW_PENDING")
    reviewed_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    # HM-02 compatibility
    @property
    def title(self) -> str:
        return self.rule_code

    @property
    def explanation(self) -> str:
        return self.description

    @property
    def recommended_action(self) -> str:
        return self.action

    @property
    def evidence_status(self) -> str:
        return self.status

    @property
    def rule_version(self) -> str:
        return self.version

    @property
    def source_name(self) -> str | None:
        return self.evidence_source

    @property
    def source_reference(self) -> str | None:
        return self.evidence_reference


class DoseRule(Base):
    __tablename__ = "dose_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    rule_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), default="ingredient")  # ingredient|product
    ingredient_id: Mapped[str | None] = mapped_column(ForeignKey("ingredients.id"), nullable=True)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    patient_criteria_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    dose_criteria_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_fields_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_type: Mapped[str] = mapped_column(String(64), default="potential_issue")
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(512), nullable=True)
    version: Mapped[str] = mapped_column(String(64), default="demo-1.0")
    status: Mapped[str] = mapped_column(String(64), default="REVIEW_PENDING")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    # Numeric convenience fields (from max_dose import / demo)
    dose_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    dose_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    dose_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    severity: Mapped[str] = mapped_column(String(32), default="MODERATE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    # HM-02 dosage_engine compatibility
    @property
    def evidence_status(self) -> str:
        return self.status

    @property
    def source_reference(self) -> str | None:
        return self.source

    @property
    def rule_version(self) -> str:
        return self.version

    @property
    def applicable_population(self) -> str:
        try:
            import json as _json

            data = _json.loads(self.patient_criteria_json or "{}")
            return str(data.get("population") or data.get("applicable_population") or "adult")
        except Exception:
            return "adult"

    @property
    def frequency_min(self) -> float | None:
        return None

    @property
    def frequency_max(self) -> float | None:
        return None


# Alias for transitional HM-02 dosage engine imports
DosageRule = DoseRule


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    review_reference: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    patient_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    age_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    context_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(64), default="draft")
    catalogue_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rule_set_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    items = relationship(
        "PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan"
    )
    reports = relationship(
        "AnalysisReport", back_populates="prescription", cascade="all, delete-orphan"
    )
    findings = relationship(
        "ReviewFinding", back_populates="prescription", cascade="all, delete-orphan"
    )


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    prescription_id: Mapped[str] = mapped_column(ForeignKey("prescriptions.id"), nullable=False)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    entered_name: Mapped[str] = mapped_column(String(255), nullable=False)
    identity_status: Mapped[str] = mapped_column(String(64), default="UNRESOLVED")
    dose_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    dose_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    route: Mapped[str | None] = mapped_column(String(64), nullable=True)
    frequency_original_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequency_structured_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Transitional fields used by HM-02 UI
    entered_brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entered_strength: Mapped[str | None] = mapped_column(String(128), nullable=True)
    frequency_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    frequency_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duration_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(64), default="unresolved")
    resolution_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    prescription = relationship("Prescription", back_populates="items")
    product = relationship("Product")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    prescription_id: Mapped[str] = mapped_column(ForeignKey("prescriptions.id"), nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    engine_version: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(64), nullable=False)
    summary_status: Mapped[str] = mapped_column(String(64), nullable=False)
    findings_json: Mapped[str] = mapped_column(Text, default="[]")
    checks_run_json: Mapped[str] = mapped_column(Text, default="[]")
    checks_not_run_json: Mapped[str] = mapped_column(Text, default="[]")
    unresolved_items_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    prescription = relationship("Prescription", back_populates="reports")
    review_events = relationship(
        "ReviewEvent", back_populates="report", cascade="all, delete-orphan"
    )


class ReviewFinding(Base):
    """Persisted finding rows (also embedded in AnalysisReport.findings_json)."""

    __tablename__ = "review_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    prescription_id: Mapped[str] = mapped_column(ForeignKey("prescriptions.id"), nullable=False)
    report_id: Mapped[str | None] = mapped_column(ForeignKey("analysis_reports.id"), nullable=True)
    finding_code: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_product_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_ingredient_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_brand_names_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_status: Mapped[str] = mapped_column(String(64), default="REVIEW_PENDING")
    source_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    rule_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rule_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_next_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_status: Mapped[str] = mapped_column(String(64), default="EVALUATED")
    why_trace_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    prescription = relationship("Prescription", back_populates="findings")


class ReviewEvent(Base):
    __tablename__ = "review_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(ForeignKey("analysis_reports.id"), nullable=False)
    finding_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # reviewed
    reviewer_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    report = relationship("AnalysisReport", back_populates="review_events")


class ApplicationSetting(Base):
    __tablename__ = "application_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    setting_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    setting_value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    minimal_metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
