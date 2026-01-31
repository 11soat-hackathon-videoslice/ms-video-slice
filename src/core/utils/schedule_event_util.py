from datetime import datetime, timedelta, timezone

from core.domain import VdscMetadata

def get_event_schedule_timestamp(vdsc_metadata: VdscMetadata, retry_backoff_factor: int) -> datetime:
    retry = int(vdsc_metadata.retries)
    delay = retry_backoff_factor * retry
    schedule_time = datetime.now(timezone.utc) + timedelta(minutes=delay)
    return schedule_time

