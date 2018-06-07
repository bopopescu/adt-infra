"""CTS test exclusions specification"""

#
# format:
#  Let
#    <test-spec> ::= <fully-qualified-class-name>#<test-method-name> in
#    <test-spec-seq> ::= '[' <test-spec> {, <test-spec> }* ']'
#    <package-spec> ::= <package> : <test-spec-seq>
#  in
#    '{' <plan> ':' '{' <package-spec> {, <package-spec> }* '}'

# Bugs for current exclusions:
#   android.trustedvoice.cts.TrustedVoiceHostTest#testLogcat: b/29270651

def cts_plans_current_exclusions():
    return { 'CTS' :
        { 'android.host.trustedvoice' :
            [ 'android.trustedvoice.cts.TrustedVoiceHostTest#testLogcat' ]
        ,
        'com.android.cts.filesystemperf' :
            [ 'com.android.cts.filesystemperf.AlmostFullTest#testRandomRead' ,
              'com.android.cts.filesystemperf.AlmostFullTest#testRandomUpdate' ,
              'com.android.cts.filesystemperf.AlmostFullTest#testSequentialUpdate' ,
              'com.android.cts.filesystemperf.RandomRWTest#testRandomRead' ,
              'com.android.cts.filesystemperf.RandomRWTest#testRandomUpdate' ,
              'com.android.cts.filesystemperf.SequentialRWTest#testSingleSequentialRead' ,
              'com.android.cts.filesystemperf.SequentialRWTest#testSingleSequentialUpdate' ,
              'com.android.cts.filesystemperf.SequentialRWTest#testSingleSequentialWrite' ]
        }
    }
