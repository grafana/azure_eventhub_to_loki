// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at

//   http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.    
//
// Copyright Grafana Labs 2024

const fs = require('fs');
const AzureFunction = require('./../index');
const { createLogLinesFromMessage,
    enrichLogLines,
    LogLine,
    detectAndSetTimeStamp,
    LokiStream,
    LokiStreamValue,
    logsLinesToLokiStreams,
    FunctionSettings,
    areJsonObjectsDelimitedByNewline,
    filterLogLines } = AzureFunction.forTests;

// load sample data from a file called sample_messages.json
const sampleStringArrayOfJsonObjects = JSON.stringify(require('./sample_messages.json'));

class TestContext {
    
    constructor() {
        this.done = jest.fn();
        this.log = new TestLogger();
    }
}

class TestLogger {

    info(message, ...optionalParams) {
        console.log(message, ...optionalParams);
    }

    warn(message, ...optionalParams) {
        console.log(message, ...optionalParams);
    }

    error(message, ...optionalParams) {
        console.log(message, ...optionalParams);
    }
}

// test that a returned record is an object with a property called userId when using the sample data
describe('createLogLinesFromMessage', () => {
    it('should return an array of records', () => {
        const context = new TestContext();

        const logLines = createLogLinesFromMessage(context, sampleStringArrayOfJsonObjects);

        // check that records is an array
        expect(Array.isArray(logLines)).toBe(true);

        // check it has two records
        expect(logLines.length).toBe(2);

        // check the expected property values
        expect(logLines[0].attributes.userId).toBe("469b775c-6ab0-48ce-b321-08dc26c3b6cf");
        expect(logLines[1].attributes.userId).toBe("178f1cf3-effb-4d07-8c2f-3a5909724164");        
    });
});

// test enrichLogLines function
describe('enrichLogLines', () => {
    it('should return an array of logLine instances with default attributes', () => {
        const context = new TestContext();

        const functionSettings = new FunctionSettings({ 'GL_DEFAULT_ATTRIBUTES': '{"defaultKey": "defaultValue","userId":"defaultUserId"}'});
        
        const logLine = new LogLine("foobar body");
        logLine.addOrUpdateAttribute('userId', '469b775c-6ab0-48ce-b321-08dc26c3b6cf');
        const enrichedLogLines = enrichLogLines([logLine], functionSettings);

        // check that records is an array
        expect(Array.isArray(enrichedLogLines)).toBe(true);

        // check it has two records
        expect(enrichedLogLines.length).toBe(1);

        // check the expected property values
        expect(enrichedLogLines[0].attributes.defaultKey).toBe("defaultValue");

        // verify that userId is not overwritten with the default value from the defaultAttributes
        expect(enrichedLogLines[0].attributes.userId).toBe("469b775c-6ab0-48ce-b321-08dc26c3b6cf");
    });
});

// test logsLinesToLokiStreams function
describe('logsLinesToLokiStreams', () => {
    it('should return an array of LokiStream instances', () => {
        const context = new TestContext();

        const functionSettings = new FunctionSettings(
            {
                'GL_DEFAULT_ATTRIBUTES': '{"source": "azure"}',
                'GL_INDEXED_ATTRIBUTES': 'userId',
                'GL_STRUCTURED_METADATA_ATTRIBUTES': 'foobar'
            });

        const logLine = new LogLine("foobar body");

        // this is an indexed stream label
        logLine.addOrUpdateAttribute('userId', '469b775c-6ab0-48ce-b321-08dc26c3b6cf');

        // this goes to structured metadata
        logLine.addOrUpdateAttribute('foobar', 'blabla');
        var logLines = [logLine];
        logLines = enrichLogLines(logLines, functionSettings);
        const lokiStreams = logsLinesToLokiStreams(logLines, functionSettings);

        // check that records is an array
        expect(Array.isArray(lokiStreams)).toBe(true);

        // check it has a single records
        expect(lokiStreams.length).toBe(1);

        // check the expected property values
        expect(lokiStreams[0].keyValuePairs.source).toBe("azure");
        expect(lokiStreams[0].keyValuePairs.userId).toBe("469b775c-6ab0-48ce-b321-08dc26c3b6cf");

        var lokiStreamValues = lokiStreams[0].getLokiStreamValues();

        // check that the LokiStreamValue has the expected structured metadata
        expect(lokiStreamValues[0].structuredMetadata).toEqual({ 'foobar': 'blabla' });   

    });
});

// test that a LokiStream returns it's LokiStreamValue's as an array sorted by timestamp ascending
describe('LokiStream', () => {
    it('should return an array of LokiStreamValue instances sorted by timestamp ascending', () => {
        const lokiStream = new LokiStream();
        // three stream values, two with a same timestamp
        const lokiStreamValue1 = new LokiStreamValue(new Date("2020-01-01T00:00:01.000Z"), "foobar body");
        const lokiStreamValue2 = new LokiStreamValue(new Date("2020-01-01T00:00:00.500Z"), "foobar body");
        const lokiStreamValue3 = new LokiStreamValue(new Date("2020-01-01T00:00:00.000Z"), "foobar body");
        lokiStream.addLokiStreamValue(lokiStreamValue2);
        lokiStream.addLokiStreamValue(lokiStreamValue1);
        lokiStream.addLokiStreamValue(lokiStreamValue3);

        const lokiStreamValues = lokiStream.getLokiStreamValues();

        // check that records is an array
        expect(Array.isArray(lokiStreamValues)).toBe(true);

        // check it has three records
        expect(lokiStreamValues.length).toBe(3);

        // check the expected property values
        expect(lokiStreamValues[0].timestamp).toEqual(new Date("2020-01-01T00:00:00.000Z"));
        expect(lokiStreamValues[1].timestamp).toEqual(new Date("2020-01-01T00:00:00.500Z"));
        expect(lokiStreamValues[2].timestamp).toEqual(new Date("2020-01-01T00:00:01.000Z"));
    });
});

// test LokiStream serialization to json
describe('LokiStream', () => {
    it('should return a json object with a keyValuePairs and lokiStreamValues properties', () => {
        const lokiStream = new LokiStream({ 'source': 'azure'});
        const lokiStreamValue1 = new LokiStreamValue(new Date("2020-01-01T00:00:00.000Z"), "foobar body");
        const lokiStreamValue2 = new LokiStreamValue(new Date("2020-01-01T00:00:00.100Z"), "foobar body");
        lokiStream.addLokiStreamValue(lokiStreamValue1);
        lokiStream.addLokiStreamValue(lokiStreamValue2);

        const lokiStreamJson = JSON.stringify(lokiStream);

        expect(lokiStreamJson).toBe('{"stream":{"source":"azure"},"values":[["1577836800000000000","foobar body",{}],["1577836800100000000","foobar body",{}]]}');
    });
});

// test FunctionSettings class validation
describe('FunctionSettings', () => {
    it('should return a FunctionSettings instance with valid values', () => {
        env = {
            'GL_API_KEY': '123',
            'GL_API_USER': '456',
            'GL_SITE': '789',
            'GL_HTTP_PATH': '123',
            'GL_HTTP_PORT': 456,
            'GL_REQUEST_TIMEOUT_MS': 789
        }

        const functionSettings = new FunctionSettings(env);
        expect(functionSettings.isValid()).toBe(true);
    });

    it('should return a FunctionSettings instance with invalid values', () => {
        env = {
            'GL_SITE': '789',
            'GL_HTTP_PATH': '123',
            'GL_HTTP_PORT': 456,
            'GL_REQUEST_TIMEOUT_MS': 789
        }

        const functionSettings = new FunctionSettings(env);
        expect(functionSettings.isValid()).toBe(false);
    });
});

// test detectAndSetTimeStamp function
describe('detectAndSetTimeStamp', () => {
    it('should return a Date instance', () => {
        const logLine = new LogLine("foobar body");
        
        const functionSettings = new FunctionSettings({ 'GL_TIMESTAMP_ATTRIBUTES':'timestamp,time,created,timeStamp'});

        logLine.addOrUpdateAttribute('timestamp', '2020-01-01T00:00:00.000Z');
        detectAndSetTimeStamp([logLine], functionSettings);
        expect(logLine.timestamp).toEqual(new Date("2020-01-01T00:00:00.000Z"));

        logLine.addOrUpdateAttribute('time', '2021-01-01T00:00:00.000Z');
        detectAndSetTimeStamp([logLine], functionSettings);
        expect(logLine.timestamp).toEqual(new Date("2021-01-01T00:00:00.000Z"));

        logLine.addOrUpdateAttribute('created', '2022-01-01T00:00:00.000Z');
        detectAndSetTimeStamp([logLine], functionSettings);
        expect(logLine.timestamp).toEqual(new Date("2022-01-01T00:00:00.000Z"));

        logLine.addOrUpdateAttribute('timeStamp', '2023-01-01T00:00:00.000Z');
        detectAndSetTimeStamp([logLine], functionSettings);
        expect(logLine.timestamp).toEqual(new Date("2023-01-01T00:00:00.000Z"));
    });
});

// test different nesting of records in sample data
describe('createLogLinesFromMessage', () => {
    it('should return an array of records', () => {
        const context = new TestContext();

        const sampleJsonWithRecords = {
            "records": [
                {
                    "userId": "469b775c-6ab0-48ce-b321-08dc26c3b6cf"
                },
                {
                    "userId": "178f1cf3-effb-4d07-8c2f-3a5909724164"
                }
            ]
        }

        const sampleStringArrayOfJsonObjects = JSON.stringify(sampleJsonWithRecords);
        
        const logLines = createLogLinesFromMessage(context, sampleStringArrayOfJsonObjects);

        // check it has two records
        expect(logLines.length).toBe(2);

        // check the expected property values
        expect(logLines[0].attributes.userId).toBe("469b775c-6ab0-48ce-b321-08dc26c3b6cf");
        expect(logLines[1].attributes.userId).toBe("178f1cf3-effb-4d07-8c2f-3a5909724164");        
    });
    it('should return an array of records when sending two objects', () => {
        const context = new TestContext();

        const sampleJsonWithRecords = {
            "records": [
                {
                    "userId": "469b775c-6ab0-48ce-b321-08dc26c3b6cf"
                },
                {
                    "userId": "178f1cf3-effb-4d07-8c2f-3a5909724164"
                }
            ]
        }

        const sampleStringArrayOfJsonObjects = JSON.stringify(sampleJsonWithRecords) + "\n" + JSON.stringify(sampleJsonWithRecords);
        
        const logLines = createLogLinesFromMessage(context, sampleStringArrayOfJsonObjects);

        // check it has two records
        expect(logLines.length).toBe(4);

        // check the expected property values
        expect(logLines[3].attributes.userId).toBe("178f1cf3-effb-4d07-8c2f-3a5909724164");
    });
    it('should return an array of records when sending a string json object', () => {
        const context = new TestContext();

        const sampleJsonWithRecords = {
            "records": [
                {
                    "userId": "469b775c-6ab0-48ce-b321-08dc26c3b6cf"
                },
                {
                    "userId": "178f1cf3-effb-4d07-8c2f-3a5909724164"
                }
            ]
        }

        const sampleJsonString = JSON.stringify(sampleJsonWithRecords);
        
        const logLines = createLogLinesFromMessage(context, sampleJsonString);

        // check it has two records
        expect(logLines.length).toBe(2);

        // check the expected property values
        expect(logLines[1].attributes.userId).toBe("178f1cf3-effb-4d07-8c2f-3a5909724164");
    });
});

// test the areJsonObjectsDelimitedByNewline function that tests if the string contains json object delimited by newline
describe('areJsonObjectsDelimitedByNewline', () => {
    it('should return true when the string contains json objects delimited by newline', () => {
        const sampleJsonWithRecords = {
            "records": [
                {
                    "userId": "469b775c-6ab0-48ce-b321-08dc26c3b6cf"
                },
                {
                    "userId": "178f1cf3-effb-4d07-8c2f-3a5909724164"
                }
            ]
        }

        const sampleStringArrayOfJsonObjects = JSON.stringify(sampleJsonWithRecords) + "\n" + JSON.stringify(sampleJsonWithRecords);

        const result = areJsonObjectsDelimitedByNewline(sampleStringArrayOfJsonObjects);

        expect(result).toBe(true);
    });

    it('should return false when the string does not contain json objects delimited by newline', () => {
        const sampleStringArrayOfJsonObjects = JSON.stringify(require('./sample_messages.json'));

        const result = areJsonObjectsDelimitedByNewline(sampleStringArrayOfJsonObjects);

        expect(result).toBe(false);
    });
});

describe('Filtering of logs through include and exclude settings', () => {
    it('should filter out logs based on the include settings', () => {
        var functionSettings = new FunctionSettings(
            { 'GL_LOG_INCLUDE_FILTER':'[{"category": "AuditEvent", "operationName": "SecretGet"}]'}
        );

        const logLine = new LogLine("foobar body");
        logLine.addOrUpdateAttribute('category', 'AuditEvent');
        logLine.addOrUpdateAttribute('operationName', 'SecretGet');
        const logLines = [logLine];
        const filteredLogLines = filterLogLines(logLines, functionSettings);

        // in include pattern, so should be included
        expect(filteredLogLines.length).toBe(1);

        functionSettings = new FunctionSettings(
            { 'GL_LOG_INCLUDE_FILTER':'[{"category": "OtherEvent"}]'}
        );

        const logLine2 = new LogLine("foobar body");
        logLine2.addOrUpdateAttribute('category', 'AuditEvent');
        logLine2.addOrUpdateAttribute('operationName', 'SecretGet');
        const logLines2 = [logLine2];
        const filteredLogLines2 = filterLogLines(logLines2, functionSettings);

        // not in include pattern, so should be excluded
        expect(filteredLogLines2.length).toBe(0);
    });
    it('should filter out logs based on the exclude settings', () => {
        var functionSettings = new FunctionSettings(
            { 'GL_LOG_EXCLUDE_FILTER':'[{"category": "AuditEvent", "operationName": "SecretGet"}]'}
        );

        const logLine = new LogLine("foobar body");
        logLine.addOrUpdateAttribute('category', 'AuditEvent');
        logLine.addOrUpdateAttribute('operationName', 'SecretGet');
        const logLines = [logLine];
        const filteredLogLines = filterLogLines(logLines, functionSettings);

        // in include pattern, so should be included
        expect(filteredLogLines.length).toBe(0);

        functionSettings = new FunctionSettings(
            { 'GL_LOG_EXCLUDE_FILTER':'[{"category": "OtherEvent"}]'}
        );

        const logLine2 = new LogLine("foobar body");
        logLine2.addOrUpdateAttribute('category', 'AuditEvent');
        logLine2.addOrUpdateAttribute('operationName', 'Not matching exclude pattern');
        const logLines2 = [logLine2];
        const filteredLogLines2 = filterLogLines(logLines2, functionSettings);

        // not in include pattern, so should be excluded
        expect(filteredLogLines2.length).toBe(1);
    });
});
