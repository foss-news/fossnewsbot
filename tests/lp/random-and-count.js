import http from 'k6/http';
import {Rate, Trend, Counter} from 'k6/metrics';
import {LOGIN, PASSWORD, TBOT_USER_ID, API_BASE_URL} from './secrets.js';

const TEST_DURATION_SECONDS = 60;
const ITERATIONS_PER_SECOND = 1;

let successRate = new Rate('Success Rate');
let durationTrend = new Trend('Requests Duration');
let requestsCounter = new Counter('Requests Counter');

export let options = {
    scenarios: {
        example_scenario: {
            executor: 'constant-arrival-rate',
            // TODO: Calculate really needed threads count
            preAllocatedVUs: 10,
            maxVUs: 10,
            rate: ITERATIONS_PER_SECOND,
            timeUnit: '1s',
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
        'username': LOGIN,
        'password': PASSWORD,
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
    const testStepsData = [
        {
            url: `${API_BASE_URL}/telegram-bot-one-random-not-categorized-foss-news-digest-record?tbot-user-id=${TBOT_USER_ID}`,
            tag: 'randomRecord',
        },
        {
            url: `${API_BASE_URL}/telegram-bot-not-categorized-foss-news-digest-records-count?tbot-user-id=${TBOT_USER_ID}`,
            tag: 'recordsCount',
        }
    ];
    for (let testStepData of testStepsData) {
        const response = http.get(testStepData.url, {headers: authHeaders}, {tags: {type: testStepData.tag}});
        successRate.add(response.status === 200, {type: testStepData.tag});
        if (response.status !== 200) {
            console.error(`${testStepData.tag} error: ${response.body}`);
        }
        durationTrend.add(response.timings.duration, {type: testStepData.tag});
        requestsCounter.add(1, {type: testStepData.tag});
        console.debug(`${testStepData.tag} response: ${response.body}`);
    }
}
