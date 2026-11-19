from app.backtest.yearly import by_year, table, year_check


def trades(year, n, net):
    return [(year, net)] * n


def test_most_years_positive_and_no_lucky_year_passes():
    rows = by_year(trades(2019, 20, 0.1) + trades(2020, 20, 0.2) + trades(2021, 20, -0.05) + trades(2022, 20, 0.1))
    c = year_check(rows)
    assert c["passed"] and c["positive_years"] == 3 and c["counting_years"] == 4


def test_half_the_years_is_not_most():
    rows = by_year(trades(2019, 20, 0.5) + trades(2020, 20, 0.5) + trades(2021, 20, -0.1) + trades(2022, 20, -0.1))
    c = year_check(rows)
    assert not c["passed"] and "only 2 of 4" in c["reasons"][0]


def test_one_lucky_year_fails():
    # 3 of 4 years positive, but all the profit is 2020.
    rows = by_year(trades(2019, 20, 0.01) + trades(2020, 20, 2.0) + trades(2021, 20, 0.01) + trades(2022, 20, -0.5))
    c = year_check(rows)
    assert not c["passed"] and "2020" in c["reasons"][0] and c["total_without_best"] < 0


def test_thin_years_are_ignored_and_too_few_years_fail():
    rows = by_year(trades(2023, 30, 0.2) + trades(2024, 5, -3.0))
    assert [r.counts for r in rows] == [True, False]
    c = year_check(rows)
    assert not c["passed"] and "not enough years" in c["reasons"][0]
    assert "2024 (too few trades)" in table(rows)


def test_validation_with_two_years_needs_both_positive():
    assert year_check(by_year(trades(2023, 15, 0.1) + trades(2024, 15, 0.2)))["passed"]
    assert not year_check(by_year(trades(2023, 15, 0.3) + trades(2024, 15, -0.1)))["passed"]
