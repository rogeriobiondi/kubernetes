import http from 'k6/http';
import { check, sleep } from 'k6';

let delta = 1;

export let options = {

    stages: [
        { duration: "10s", target: (delta * 1) },
        { duration: "5s", target: (delta * 1) },

        { duration: "10s", target: (delta * 2) },
        { duration: "5s", target: (delta * 2) },

        { duration: "10s", target: (delta * 3) },
        { duration: "5s", target: (delta * 3) },

        { duration: "10s", target: (delta * 4) },
        { duration: "5s", target: (delta * 4) },

        { duration: "10s", target: (delta * 5) },
        { duration: "5s", target: (delta * 5) },

        { duration: "10s", target: (delta * 6) },
        { duration: "5s", target: (delta * 6) },

        { duration: "10s", target: (delta * 7) },
        { duration: "5s", target: (delta * 7) },

        { duration: "10s", target: (delta * 8) },
        { duration: "5s", target: (delta * 8) },

        { duration: "10s", target: (delta * 9) },
        { duration: "5s", target: (delta * 9) },

        { duration: "10s", target: (delta * 10) },
        { duration: "5s", target: (delta * 10) },

        { duration: "2s", target: (delta * 10) },
        { duration: "2s", target: (delta * 9) },
        { duration: "2s", target: (delta * 8) },
        { duration: "2s", target: (delta * 7) },
        { duration: "2s", target: (delta * 6) },
        { duration: "2s", target: (delta * 5) },
        { duration: "2s", target: (delta * 4) },
        { duration: "2s", target: (delta * 3) },
        { duration: "2s", target: (delta * 2) },
        { duration: "2s", target: (delta * 1) },
        { duration: "2s", target: (delta * 0) }
    ]
};

export default function () {

    let url = `http://localhost:30333/v1/tracking/AM037392733LO?moderated=false`
    let response = http.get(url);

    check(response, {
        '{"detail":"Package AM037392733LO not found on the tracking system."}': (r) => r.status === 200
    });

    sleep(1);
};