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

const { log } = require('console');
const https = require('https');


class FunctionSettings {
    constructor (env) {
        this.GL_API_KEY = env.GL_API_KEY || '<GRAFANA_CLOUD_API_KEY>';
        this.GL_API_USER = env.GL_API_USER || '<GRAFANA_CLOUD_API_USER>';
        this.GL_SITE = env.GL_SITE || 'logs-prod-013.grafana.net';
        this.GL_HTTP_PATH = env.GL_URL || '/loki/api/v1/push';
        this.GL_HTTP_PORT = env.GL_PORT || 443;
        this.GL_REQUEST_TIMEOUT_MS = 10000;
        this.GL_TIMESTAMP_ATTRIBUTES = (env.GL_TIMESTAMP_ATTRIBUTES || 'timeStamp,timestamp,time,created').split(',');
        this.GL_INDEXED_ATTRIBUTES = (env.GL_INDEXED_ATTRIBUTES || 'source,sourceType,resourceId').split(',');
        this.GL_STRUCTURED_METADATA_ATTRIBUTES = (env.GL_STRUCTURED_METADATA_ATTRIBUTES || 'ActivityId').split(',');
        this.GL_DEFAULT_ATTRIBUTES = JSON.parse(env.GL_DEFAULT_ATTRIBUTES || '{"source":"azure","sourceType":"eventHub"}');
        this.GL_LOG_INCLUDE_FILTER =  JSON.parse(env.GL_LOG_INCLUDE_FILTER || '[]');
        this.GL_LOG_EXCLUDE_FILTER = JSON.parse(env.GL_LOG_EXCLUDE_FILTER || '[]');
    }

    isValid () {
        // TODO add more check for the other environment variables.
        return this.GL_API_KEY !== '<GRAFANA_CLOUD_API_KEY>' &&
            this.GL_API_USER !== '<GRAFANA_CLOUD_API_USER>';
    }
}

class LogLine {
    constructor (body) {
        this.body = body;
        this.timestamp = new Date();
        this.attributes = {};
    }

    addOrUpdateAttribute (name, value) {
        this.attributes[name] = value;
    }

    modifyAttribute (name, value) {
        this.attributes[name] = value;
    }

    setTimestamp (timestamp) {
        this.timestamp = timestamp;
    }
}

class LokiStream {
    constructor (keyValuePairs = {}, lokiStreamValues = []) {
        this.keyValuePairs = keyValuePairs;
        this.lokiStreamValues = lokiStreamValues;
    }

    addKeyValuePair (key, value) {
        this.keyValuePairs[key] = value;
    }

    addLokiStreamValue (lokiStreamValue) {
        this.lokiStreamValues.push(lokiStreamValue);
    }

    getKeyValuePairs () {
        return this.keyValuePairs;
    }

    getLokiStreamValues () {
        // return a sorted list of the stream values by timestamp ascending
       return this.lokiStreamValues.sort((a, b) => a.timestamp - b.timestamp);
    }

    toJSON () {
        return {
            stream: this.keyValuePairs,
            values: this.getLokiStreamValues()
        };
    }
}

class LokiStreamValue {
    constructor (timestamp, rawLogLine, structuredMetadata = {}) {
        this.timestamp = timestamp;
        this.rawLogLine = rawLogLine;
        this.structuredMetadata = structuredMetadata;
    }

    toJSON () {
        // stringify the rawLogLine if it's an object
        const rawLogLineStr = typeof this.rawLogLine === 'object' ? JSON.stringify(this.rawLogLine) : this.rawLogLine;

        return [(this.timestamp * 1000000).toString(), rawLogLineStr, this.structuredMetadata];
    }
}

// regex to match strings that contain json objects delimited by a newline
function areJsonObjectsDelimitedByNewline (str) {
    // check of the string starts with a curly brace and ends with a curly brace
    trimmed_str = str.trim();
    if (trimmed_str.startsWith('{') && trimmed_str.endsWith('}')) {
        // check if there are one or more occurence of a close curly brace followed by a newline and a curly brace close
        return /}.*?\n{/.test(trimmed_str);
    } else {
        return false;
    }
}

function createLogLinesFromMessage (context, eventHubMessage) {
    // assert that eventHubMessage is a string
    if (typeof eventHubMessage !== 'string') {
        throw new Error('The message is not a string');
    }

    if (areJsonObjectsDelimitedByNewline(eventHubMessage)) {        
        var messagesArray = eventHubMessage.split('\n');
        // remove empty strings from the array
        messagesArray = messagesArray.filter(message => message.trim() !== '');

        return messagesArray.flatMap(message => createLogLinesFromMessage(context, message));
    }

    // try to parse the eventHubMessages as a JSON object
    try {
        const messages = JSON.parse(eventHubMessage);

        // if the message is an array, with javascript objects, then map the objects to records
        if (Array.isArray(messages)) {
            return messages.map(message => {
                // serialize the message from json to a string
                const logLine = new LogLine(message);

                // add all the key value pairs of the json to the logLine
                for (const key in message) {
                    logLine.addOrUpdateAttribute(key, message[key]);
                }

                return logLine;
            });
        } else if (typeof messages === 'object' && 'records' in messages) {
            // create loglines from the nested records
            return createLogLinesFromMessage(context, JSON.stringify(messages.records));
        } else {
            throw new Error('The message is of an unsupported structure, Not implemented.');
        }
    } catch (error) {
        context.log.warn('The message is not a JSON object');
        context.log.info(eventHubMessage)
        // use the full message as a record
        return [new LogLine(eventHubMessage)];
    }

    // unreachable code
}

function enrichLogLines (logLines, functionSettings) {
    // loop through all the records
    logLines.forEach(logLine => {
        // add default attributes to the record when there is not a value set yet
        for (const key in functionSettings.GL_DEFAULT_ATTRIBUTES) {
            if (!(key in logLine.attributes)) {
                logLine.addOrUpdateAttribute(key, functionSettings.GL_DEFAULT_ATTRIBUTES[key]);
            }
        }
    });

    return logLines;
}

function logsLinesToLokiStreams (logLines, functionSettings) {
    const lokiStreams = [];

    // loop through all the records
    logLines.forEach(logLine => {
        // get the values of the default attribute keys from the logline attributes
        const streamkeyValuePairs = {};
        for (const key in functionSettings.GL_DEFAULT_ATTRIBUTES) {
            streamkeyValuePairs[key] = logLine.attributes[key];
        }

        // promote any indexed attributes to the stream key value pairs, if it is part of the logline attributes
        functionSettings.GL_INDEXED_ATTRIBUTES.forEach(indexedAttribute => {
            if (indexedAttribute in logLine.attributes) {
                streamkeyValuePairs[indexedAttribute] = logLine.attributes[indexedAttribute];
            }
        });

        // attributes that are not used as stream key value pairs are added as structured metadata
        const structuredMetadata = {};

        for (const key in logLine.attributes) {

            if (!(key in streamkeyValuePairs) && functionSettings.GL_STRUCTURED_METADATA_ATTRIBUTES.includes(key)) {
                structuredMetadata[key] = logLine.attributes[key];
            }
        }

        // check if there is already a lokiStream with the same key value pairs
        let lokiStream = lokiStreams.find(stream => {
            return stream.getKeyValuePairs() === streamkeyValuePairs;
        });

        // none found, init a new one
        if (lokiStream === undefined) {
            lokiStream = new LokiStream(streamkeyValuePairs);
            lokiStreams.push(lokiStream);
        }

        // add the logline to the loki stream as a loki stream value
        // TODO, figure out what to add as structured metadata
        lokiStream.addLokiStreamValue(new LokiStreamValue(logLine.timestamp, logLine.body, structuredMetadata));
    });

    return lokiStreams;
}

// include or exclude loglines based on the filter settings
function filterLogLines (logLines, functionSettings) {
    // filter out loglines that do not match the include filter

    logLines = logLines.filter(logLine => {
        for (const filter of functionSettings.GL_LOG_INCLUDE_FILTER) {
            // e.g. filter = { 'category': 'AuditEvent', 'operationName': 'SecretGet' }
            for (const key of Object.keys(filter)) {
                if (!(key in logLine.attributes) || logLine.attributes[key] !== filter[key]) {
                    // logline does not match the filter, should be excluded
                    return false;
                }
            }
        }
        return true;
    });

    logLines = logLines.filter(logLine => {
        for (const filter of functionSettings.GL_LOG_EXCLUDE_FILTER) {
            // e.g. filter = { 'category': 'AuditEvent', 'operationName': 'SecretGet' }
            for (const key of Object.keys(filter)) {
                if (key in logLine.attributes && logLine.attributes[key] === filter[key]) {
                    // logline does not match the filter, should be excluded
                    return false;
                }
            }
        }

        return true;
    });

    return logLines;
}

function detectAndSetTimeStamp (logLines, functionSettings) {
    // loop through all the loglines
    logLines.forEach(logLine => {
        // check if there is a timestamp attribute in the logline
        for (const key in logLine.attributes) {
            if (functionSettings.GL_TIMESTAMP_ATTRIBUTES.includes(key)) {
                // set the timestamp of the logline to the value of the timestamp attribute
                logLine.setTimestamp(new Date(logLine.attributes[key]));
            }
        }
    });
    return logLines;
}

function sendStreamsToAPI (context, functionSettings, streams) {
    context.log('Sending json to API');

    const json = JSON.stringify(streams);

    context.log(json);

    try {
        // send json to an http API endpoints
        const options = {
            hostname: functionSettings.GL_SITE,
            port: functionSettings.GL_HTTP_PORT,
            path: functionSettings.GL_HTTP_PATH,
            method: 'POST',
            auth: functionSettings.GL_API_USER + ':' + functionSettings.GL_API_KEY,
            headers: {
                'Content-Type': 'application/json'
            },
            timeout: functionSettings.GL_REQUEST_TIMEOUT_MS
        };

        const req = https.request(options, resp => {
            context.log('Request response status code: ', resp.statusCode);

            // write the body to the console
            resp.on('data', d => {
                context.log(d.toString());
            });

            context.done();
        })
            .on('error', error => {
                context.log(`Request error: ${error.message}`);
            })
            .on('timeout', () => {
                req.destroy();
                context.log('Request timeout');
            });

        req.write(json);
        req.end();

        // sleep 10 seconds
    } catch (error) {
        context.log.error(`Error: ${error.message}`);
    }

    context.log('Sent json to API');
}

function processMessages (context, functionSettings, eventHubMessages) {
    // verify that the function settings are valid
    if (!functionSettings.isValid()) {
        throw new Error('Function settings are invalid');
    }

     // every message is processed and returns one or more records in an array
     let logLines = eventHubMessages.flatMap(message => {
        context.log('message received: ', message);
        // log type of the message
        context.log('message type: ', typeof message);
        return createLogLinesFromMessage(context, message);
    });

    logLines = filterLogLines(logLines, functionSettings);
    logLines = enrichLogLines(logLines, functionSettings);
    logLines = detectAndSetTimeStamp(logLines, functionSettings);
    const lokiStreams = logsLinesToLokiStreams(logLines, functionSettings);

    // prepare json to send to the API
    const streams = {
        streams: lokiStreams.map(stream => stream.toJSON())
    };

    // records are then send to an api
     sendStreamsToAPI(context, functionSettings, streams);
}

module.exports = function (context, eventHubMessages) {
    processMessages(
        context,
        new FunctionSettings(process.env),
        eventHubMessages
    );
};

module.exports.forTests = {
    createLogLinesFromMessage,
    enrichLogLines,
    LogLine,
    detectAndSetTimeStamp,
    LokiStream,
    LokiStreamValue,
    logsLinesToLokiStreams,
    FunctionSettings,
    areJsonObjectsDelimitedByNewline,
    filterLogLines
};
