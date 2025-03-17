def _compute_status(features) -> str:
    all_status = set([feature.result.status for feature in features])
    if all_status == [CucumberStatus.passed]:
        return CucumberStatus.passed
    for status in [
        CucumberStatus.failed,
        CucumberStatus.skipped,
        CucumberStatus.pending,
        CucumberStatus.undefined,
    ]:
        if status in all_status:
            return status
    return CucumberStatus.unknown


def compute_aggregate_results(
    features: List[CucumberFeature],
) -> CucumberAggregatedResult:
    return CucumberAggregatedResult(
        status=_compute_status(features),
        duration=sum([feature.result.duration for feature in features]),
        nb_scenarii=sum([feature.result.nb_scenarii for feature in features]),
        nb_passed=sum([feature.result.nb_passed for feature in features]),
        start_timestamp=(
            None if features == [] else features[0].aggregate_result.start_timestamp
        ),
    )
