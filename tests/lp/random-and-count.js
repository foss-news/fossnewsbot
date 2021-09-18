import http from 'k6/http';
import {Rate, Trend, Counter} from 'k6/metrics';
import {login, password} from './secrets.js';

const API_BASE_URL = 'https://fn.permlug.org/api/v1';
const TEST_DURATION_SECONDS = 60;
const ITERATIONS_PER_SECOND = 1;

let successRate = new Rate('Success Rate');
let durationTrend = new Trend('Requests Duration');
let requestsCounter = new Counter('Requests Counter');

export let options = {
    scenarios: {
        // To make some advanced options available we need to make more complicated
        // options structure
        example_scenario: {
            // Constant rate, not VUs (see docs https://k6.io/docs/using-k6/scenarios/executors/)
            executor: 'constant-arrival-rate',
            // TODO: Calculate needed threads count
            preAllocatedVUs: 10,
            maxVUs: 10,
            rate: ITERATIONS_PER_SECOND,
            timeUnit: '1s',
            // We still don't want to wait much
            duration: `${TEST_DURATION_SECONDS}s`,
            gracefulStop: '2s',
        }
    },
    thresholds: {
        'Success Rate{type:randomRecord}': ['rate > 0.999'],
        'Requests Duration{type:randomRecord}': ['p(95) < 100'],
        'Requests Counter{type:randomRecord}': [`count >= ${TEST_DURATION_SECONDS * ITERATIONS_PER_SECOND / 2}`],
        'Success Rate{type:recordsCount}': ['rate > 0.999'],
        'Requests Duration{type:recordsCount}': ['p(95) < 100'],
        'Requests Counter{type:recordsCount}': [`count >= ${TEST_DURATION_SECONDS * ITERATIONS_PER_SECOND / 2}`],
    },
    summaryTrendStats: [
        'min',
        'avg',
        'med',
        'max',
        'p(75)',
        'p(90)',
        'p(95)',
        'p(99)',
    ],
};

export function setup() {
    const authRequestData = {
        'username': login,
        'password': password,
    };
    const authRequestDataJson = JSON.stringify(authRequestData);
    const authRequestHeaders = {
        'Content-type': 'application/json',
    }
    const authResponse = http.post(`${API_BASE_URL}/token/`, authRequestDataJson, {'headers': authRequestHeaders});
    if (authResponse.status !== 200) {
        console.error(`Failed to authenticate: ${authResponse.body}`);
        return;
    }
    const authToken = JSON.parse(authResponse.body)['access'];
    return authToken;
}

export default function(data) {
    const authToken = data;
    const authHeaders = {
        Authorization: `Bearer ${authToken}`,
    };
    const randomDigestRecordUrl = `${API_BASE_URL}/telegram-bot-one-random-not-categorized-foss-news-digest-record`;
    const randomDigestRecordResponse = http.get(randomDigestRecordUrl, {headers: authHeaders}, {tags: {type: 'randomRecord'}});
    successRate.add(randomDigestRecordResponse.status === 200, {type: 'randomRecord'});
    durationTrend.add(randomDigestRecordResponse.timings.duration, {type: 'randomRecord'});
    requestsCounter.add(1, {type: 'randomRecord'});
    const digestRecordsCountUrl = `${API_BASE_URL}/telegram-bot-not-categorized-foss-news-digest-records-count`;
    const digestRecordsCountResponse = http.get(randomDigestRecordUrl, {headers: authHeaders}, {tags: {type: 'recordsCount'}});
    successRate.add(digestRecordsCountResponse.status === 200, {type: 'recordsCount'});
    durationTrend.add(digestRecordsCountResponse.timings.duration, {type: 'recordsCount'});
    requestsCounter.add(1, {type: 'recordsCount'});
}
