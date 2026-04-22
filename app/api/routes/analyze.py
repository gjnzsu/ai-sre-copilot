from fastapi import APIRouter, Depends

from app.api.schemas.request import AnalyzeRequest
from app.api.schemas.response import AnalyzeResponse
from app.application.services.analyze_batch_service import AnalyzeBatchService
from app.config.settings import Settings, get_settings
from app.infrastructure.detection.robust_spike_detector import RobustSpikeDetector
from app.infrastructure.normalizers.gcp_logging_normalizer import GCPLoggingNormalizer
from app.infrastructure.normalizers.text_normalizer import TextNormalizer
from app.infrastructure.pattern.template_pattern_miner import TemplatePatternMiner

router = APIRouter()


def get_analyze_service(settings: Settings = Depends(get_settings)) -> AnalyzeBatchService:
    return AnalyzeBatchService(
        gcp_normalizer=GCPLoggingNormalizer(),
        text_normalizer=TextNormalizer(),
        detector=RobustSpikeDetector(
            default_window_size=settings.window_size,
            min_error_count=settings.min_error_count,
            min_spike_ratio=settings.min_spike_ratio,
            robust_z_threshold=settings.robust_z_threshold,
        ),
        pattern_miner=TemplatePatternMiner(),
    )


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_logs(
    request: AnalyzeRequest,
    service: AnalyzeBatchService = Depends(get_analyze_service),
) -> AnalyzeResponse:
    return service.analyze(request)
