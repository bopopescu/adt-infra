def enum(**enums):
    return type('Enum', (), enums)

VerifiedLabels = enum (TEST_FAILING = -2,
                       BUILD_FAILING = -1,
                       NO_SCORE = 0,
                       BUILT_NOT_TESTED = 1,
                       BUILT_AND_TESTED = 2)
