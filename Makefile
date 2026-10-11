.PHONY: install test cpp regression demo lint all clean

install:
	python3 -m pip install -e '.[dev]'

test:
	pytest -q

cpp:
	cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release
	cmake --build cpp/build --parallel
	ctest --test-dir cpp/build --output-on-failure

regression:
	python -m automotive_can regression --output reports/latest

demo:
	python -m automotive_can demo

lint:
	ruff check src tests

all: test cpp regression

clean:
	rm -rf cpp/build reports/latest .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
