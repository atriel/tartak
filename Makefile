CPP=g++
CPPFLAGS=-std=c++11

.PHONY: test

test:
	python3 tests/tests.py --verbose --failfast --catch
