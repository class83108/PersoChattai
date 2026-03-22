"""NLP 量化指標計算測試。"""

from __future__ import annotations

from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

from persochattai.assessment.nlp import NlpAnalyzer
from persochattai.assessment.schemas import NlpMetrics

_spacy_available = NlpAnalyzer()._nlp is not None
pytestmark = pytest.mark.skipif(not _spacy_available, reason='spacy en_core_web_sm 未安裝')

scenarios('features/nlp_metrics.feature')


# --- Fixtures ---


@pytest.fixture
def analyzer() -> NlpAnalyzer:
    return NlpAnalyzer()


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


# --- Rule: 完整指標計算 ---


@given('一段包含多句英文的 transcript 至少 100 tokens')
def long_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = (
        'I went to the store yesterday because I needed to buy some groceries. '
        'Although it was raining heavily, I decided to walk instead of taking the bus. '
        'The store was quite crowded, and I had to wait in a long line. '
        'I bought some vegetables, fruits, and a few cans of soup. '
        'When I got home, I realized that I had forgotten to buy milk. '
        'So I had to go back to the store again, which was quite annoying. '
        'However, the second trip was much faster because the rain had stopped. '
        'I also met my neighbor who told me about a new restaurant in the area. '
        'We decided to try it out next weekend if the weather is nice. '
        'Overall, it was a productive but tiring day of shopping.'
    )


@when('執行 NLP 分析', target_fixture='metrics')
def run_nlp_analysis(analyzer: NlpAnalyzer, ctx: dict[str, Any]) -> NlpMetrics:
    return analyzer.analyze(ctx['text'])


@then('回傳 NlpMetrics 包含 mtld vocd_d k1_ratio k2_ratio awl_ratio')
def check_lexical_metrics(metrics: NlpMetrics) -> None:
    assert metrics.mtld is not None
    assert metrics.vocd_d is not None
    assert metrics.k1_ratio is not None
    assert metrics.k2_ratio is not None
    assert metrics.awl_ratio is not None


@then('回傳 NlpMetrics 包含 avg_sentence_length conjunction_ratio self_correction_count')
def check_fluency_metrics(metrics: NlpMetrics) -> None:
    assert metrics.avg_sentence_length is not None
    assert metrics.conjunction_ratio is not None
    assert metrics.self_correction_count is not None


@then('回傳 NlpMetrics 包含 subordinate_clause_ratio tense_diversity grammar_error_count')
def check_grammar_metrics(metrics: NlpMetrics) -> None:
    assert metrics.subordinate_clause_ratio is not None
    assert metrics.tense_diversity is not None
    assert metrics.grammar_error_count is not None


# --- Rule: 詞彙多樣性指標 ---


@given('一段至少 50 tokens 的英文 transcript')
def medium_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = (
        'Learning a new language requires dedication and consistent practice every single day. '
        'You need to expose yourself to different materials like books, podcasts, and movies regularly. '
        'Speaking with native speakers is incredibly valuable for improving your fluency and confidence. '
        'Grammar rules are important but should not be the only focus of your studies and practice sessions.'
    )


@then('mtld 為正數')
def check_mtld_positive(metrics: NlpMetrics) -> None:
    assert metrics.mtld is not None
    assert metrics.mtld > 0


@then('vocd_d 為正數')
def check_vocd_d_positive(metrics: NlpMetrics) -> None:
    assert metrics.vocd_d is not None
    assert metrics.vocd_d > 0


# --- Rule: 詞頻分佈分析 ---


@given('一段包含混合難度詞彙的 transcript')
def mixed_vocab_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = (
        'The empirical analysis of linguistic methodology requires a comprehensive approach. '
        'We need to examine the hypothesis from multiple perspectives. '
        'The cat sat on the mat and looked at the dog in the garden. '
        'I went to school yesterday and had a good time with friends.'
    )


@then('k1_ratio 和 k2_ratio 和 awl_ratio 各自介於 0.0 至 1.0')
def check_ratios_range(metrics: NlpMetrics) -> None:
    assert 0.0 <= metrics.k1_ratio <= 1.0
    assert 0.0 <= metrics.k2_ratio <= 1.0
    assert 0.0 <= metrics.awl_ratio <= 1.0


@then('三者之和不超過 1.0')
def check_ratios_sum(metrics: NlpMetrics) -> None:
    assert metrics.k1_ratio + metrics.k2_ratio + metrics.awl_ratio <= 1.0


# --- Rule: 自我修正偵測 ---


@given('transcript 包含 "I went to... I mean, I was going to the store. No wait, the mall."')
def self_correction_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = 'I went to... I mean, I was going to the store. No wait, the mall.'


@then('self_correction_count 至少為 2')
def check_self_correction_count(metrics: NlpMetrics) -> None:
    assert metrics.self_correction_count >= 2


@given('transcript 包含 "I enjoy reading books every day."')
def no_correction_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = 'I enjoy reading books every day.'


@then('self_correction_count 為 0')
def check_no_self_correction(metrics: NlpMetrics) -> None:
    assert metrics.self_correction_count == 0


# --- Rule: 語法分析 ---


@given('transcript 包含 "Although it was raining, I went out because I needed groceries."')
def subordinate_clause_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = 'Although it was raining, I went out because I needed groceries.'


@then('subordinate_clause_ratio 大於 0')
def check_subordinate_ratio(metrics: NlpMetrics) -> None:
    assert metrics.subordinate_clause_ratio > 0


@given(
    'transcript 包含 "I went to the store yesterday. '
    'I have been studying English. I will travel next week."'
)
def multi_tense_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = (
        'I went to the store yesterday. I have been studying English. I will travel next week.'
    )


@then('tense_diversity 大於 1')
def check_tense_diversity(metrics: NlpMetrics) -> None:
    assert metrics.tense_diversity > 1


# --- Rule: 輸入邊界 ---


@given('一段少於 50 tokens 的短 transcript')
def short_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = 'Hello, how are you today?'


@then('mtld 為 None')
def check_mtld_none(metrics: NlpMetrics) -> None:
    assert metrics.mtld is None


@then('vocd_d 為 None')
def check_vocd_d_none(metrics: NlpMetrics) -> None:
    assert metrics.vocd_d is None


@then('其餘指標正常計算')
def check_other_metrics_exist(metrics: NlpMetrics) -> None:
    assert metrics.k1_ratio is not None
    assert metrics.avg_sentence_length is not None
    assert metrics.self_correction_count is not None


@given('transcript 為空字串')
def empty_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = ''


@then('所有數值指標為 0 或 None')
def check_all_zero_or_none(metrics: NlpMetrics) -> None:
    assert metrics.mtld is None or metrics.mtld == 0
    assert metrics.vocd_d is None or metrics.vocd_d == 0
    assert metrics.k1_ratio == 0.0
    assert metrics.avg_sentence_length == 0.0
    assert metrics.self_correction_count == 0


# --- Rule: Edge Cases ---


@given('transcript 為 "the the the the the the the the the the" 重複 20 次')
def repetitive_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = ' '.join(['the the the the the the the the the the'] * 20)


@then('mtld 小於 20')
def check_low_mtld(metrics: NlpMetrics) -> None:
    assert metrics.mtld is not None
    assert metrics.mtld < 20


@given('transcript 包含大量學術詞彙如 "analyze hypothesis methodology empirical"')
def academic_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = (
        'The analyze of this hypothesis requires rigorous methodology. '
        'The empirical evidence suggests a significant correlation. '
        'We must evaluate the conceptual framework and its implications. '
        'The research demonstrates substantial theoretical contributions.'
    )


@then('awl_ratio 大於 0.1')
def check_high_awl(metrics: NlpMetrics) -> None:
    assert metrics.awl_ratio > 0.1


# --- Rule: 輸出契約 ---


@given('一段正常長度的 transcript')
def normal_transcript(ctx: dict[str, Any]) -> None:
    ctx['text'] = (
        'I went to the store yesterday because I needed to buy some groceries. '
        'Although it was raining heavily, I decided to walk instead of taking the bus. '
        'The store was quite crowded, and I had to wait in a long line. '
        'I bought some vegetables, fruits, and a few cans of soup. '
        'When I got home, I realized that I had forgotten to buy milk.'
    )


@then('mtld 為 float 或 None')
def check_mtld_type(metrics: NlpMetrics) -> None:
    assert metrics.mtld is None or isinstance(metrics.mtld, float)


@then('vocd_d 為 float 或 None')
def check_vocd_d_type(metrics: NlpMetrics) -> None:
    assert metrics.vocd_d is None or isinstance(metrics.vocd_d, float)


@then('k1_ratio k2_ratio awl_ratio 為 float')
def check_ratio_types(metrics: NlpMetrics) -> None:
    assert isinstance(metrics.k1_ratio, float)
    assert isinstance(metrics.k2_ratio, float)
    assert isinstance(metrics.awl_ratio, float)


@then('avg_sentence_length 為 float')
def check_avg_sentence_type(metrics: NlpMetrics) -> None:
    assert isinstance(metrics.avg_sentence_length, float)


@then('conjunction_ratio 為 float')
def check_conjunction_type(metrics: NlpMetrics) -> None:
    assert isinstance(metrics.conjunction_ratio, float)


@then('subordinate_clause_ratio 為 float')
def check_subordinate_type(metrics: NlpMetrics) -> None:
    assert isinstance(metrics.subordinate_clause_ratio, float)


@then('self_correction_count 為 int')
def check_self_correction_type(metrics: NlpMetrics) -> None:
    assert isinstance(metrics.self_correction_count, int)


@then('tense_diversity 為 int')
def check_tense_diversity_type(metrics: NlpMetrics) -> None:
    assert isinstance(metrics.tense_diversity, int)


@then('grammar_error_count 為 int')
def check_grammar_error_type(metrics: NlpMetrics) -> None:
    assert isinstance(metrics.grammar_error_count, int)


@then('所有 ratio 值介於 0.0 至 1.0')
def check_all_ratios_range(metrics: NlpMetrics) -> None:
    assert 0.0 <= metrics.k1_ratio <= 1.0
    assert 0.0 <= metrics.k2_ratio <= 1.0
    assert 0.0 <= metrics.awl_ratio <= 1.0
    assert 0.0 <= metrics.conjunction_ratio <= 1.0
    assert 0.0 <= metrics.subordinate_clause_ratio <= 1.0


@then('所有 count 值大於等於 0')
def check_all_counts_nonneg(metrics: NlpMetrics) -> None:
    assert metrics.self_correction_count >= 0
    assert metrics.tense_diversity >= 0
    assert metrics.grammar_error_count >= 0
