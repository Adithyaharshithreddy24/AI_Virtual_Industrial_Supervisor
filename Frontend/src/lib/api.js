const API_URL =
    import.meta.env.VITE_BACKEND_URL ||
    "http://localhost:8000";


async function request(
    path,
    options = {}
) {

    const token =
        localStorage.getItem(
            "access_token"
        );


    const isFormData =
        options.body instanceof FormData;


    let response;

    try {
        response =
            await fetch(
                `${API_URL}${path}`,
                {
                    ...options,

                    headers: {

                    ...(isFormData
                        ? {}
                        : {
                            "Content-Type":
                                "application/json",
                        }),

                    ...(token
                        ? {
                            Authorization:
                                `Bearer ${token}`,
                        }
                        : {}),

                        ...(options.headers ||
                            {}),
                    },
                }
            );
    } catch (error) {
        throw new Error(
            `Unable to reach the backend at ${API_URL}. ` +
            "Check that the backend is running and the URL is correct."
        );
    }


    const contentType =
        response.headers.get(
            "content-type"
        ) || "";


    const data =
        contentType.includes(
            "application/json"
        )
            ? await response.json()
            : await response.text();


    if (!response.ok) {

        throw new Error(
            typeof data === "object"
                ? data.detail ||
                  "Request failed"
                : data ||
                  "Request failed"
        );
    }


    return data;
}


export const api = {


    // =================================================
    // AUTH
    // =================================================

    login: (
        username,
        password
    ) => {

        const params =
            new URLSearchParams();

        params.set(
            "username",
            username
        );

        params.set(
            "password",
            password
        );


        return request(
            `/api/v1/auth/login?${params.toString()}`,
            {
                method: "POST",
            }
        );
    },


    // =================================================
    // WORKERS
    // =================================================

    getWorkers: () =>
        request(
            "/api/v1/workers"
        ),


    addWorker: (
        worker
    ) =>
        request(
            "/api/v1/workers",
            {
                method: "POST",
                body: JSON.stringify(
                    worker
                ),
            }
        ),


    // =================================================
    // MACHINES
    // =================================================

    getMachines: () =>
        request(
            "/api/v1/machines"
        ),


    getMachine: (
        machineId
    ) =>
        request(
            `/api/v1/machines/${machineId}`
        ),


    addMachine: async ({
        name,
        manufacturer,
        model,
        technician_id,
        user_manual,
    }) => {

        const formData =
            new FormData();


        formData.append(
            "name",
            name
        );

        formData.append(
            "manufacturer",
            manufacturer
        );

        formData.append(
            "model",
            model
        );

        formData.append(
            "technician_id",
            technician_id
        );


        if (user_manual) {

            formData.append(
                "user_manual",
                user_manual
            );
        }


        return request(
            "/api/v1/machines",
            {
                method: "POST",
                body: formData,
            }
        );
    },


    // =================================================
    // ISSUES
    // =================================================

    getIssues: () =>
        request(
            "/api/v1/issues"
        ),


    getIssue: (
        issueId
    ) =>
        request(
            `/api/v1/issues/${issueId}`
        ),


    workerDashboard: (
        workerId
    ) =>
        request(
            `/api/v1/issues?worker_id=${encodeURIComponent(
                workerId
            )}`
        ),


    technicianDashboard: (
        technicianId
    ) =>
        request(
            `/api/v1/issues?technician_id=${encodeURIComponent(
                technicianId
            )}`
        ),


    createIssue: (
        issue
    ) =>
        request(
            "/api/v1/issues",
            {
                method: "POST",
                body: JSON.stringify(
                    issue
                ),
            }
        ),


    updateIssue: (
        issueId,
        update,
        technicianId = null
    ) =>
        request(
            `/api/v1/issues/${issueId}${
                technicianId
                    ? `?technician_id=${encodeURIComponent(
                        technicianId
                    )}`
                    : ""
            }`,
            {
                method: "PATCH",
                body: JSON.stringify(
                    update
                ),
            }
        ),


    // =================================================
    // AI ISSUE ANALYSIS
    // =================================================

    analyzeIssue: (
        message,
        domainFilter = null,
        workerId = null,
        machineId = null,
        issueId = null
    ) =>
        request(
            "/api/v1/issues/analyze",
            {
                method: "POST",

                body: JSON.stringify({
                    message,
                    domain_filter:
                        domainFilter,
                    worker_id:
                        workerId,
                    machine_id:
                        machineId,
                    issue_id:
                        issueId,
                }),
            }
        ),


    // =================================================
    // VOICE
    // =================================================

    analyzeVoice: async (
        audioBlob,
        domainFilter = null,
        workerId = null,
        machineId = null,
        issueId = null
    ) => {

        const formData =
            new FormData();


        formData.append(
            "file",
            audioBlob,
            "worker_voice.webm"
        );


        const params =
            new URLSearchParams();


        if (domainFilter) {

            params.set(
                "domain_filter",
                domainFilter
            );
        }


        if (workerId) {

            params.set(
                "worker_id",
                workerId
            );
        }


        if (machineId) {

            params.set(
                "machine_id",
                machineId
            );
        }

        if (issueId) {

            params.set(
                "issue_id",
                issueId
            );
        }


        const query =
            params.toString();


        return request(
            `/api/v1/voice/analyze${
                query
                    ? `?${query}`
                    : ""
            }`,
            {
                method: "POST",
                body: formData,
            }
        );
    },


    synthesizeSpeech: (
        text,
        languageCode = "en-IN"
    ) => {
        const params = new URLSearchParams({
            text,
            language_code: languageCode,
        });

        return fetch(
            `${API_URL}/api/v1/voice/synthesize?${params}`,
            {
                headers: {
                    ...(localStorage.getItem(
                        "access_token"
                    )
                        ? {
                            Authorization:
                                `Bearer ${localStorage.getItem(
                                    "access_token"
                                )}`,
                        }
                        : {}),
                },
            }
        ).then(async (response) => {
            if (!response.ok) {
                const detail = await response.text();
                throw new Error(
                    detail || "Speech synthesis failed"
                );
            }
            return response.blob();
        });
    },


    transcribeVoice: async (
        audioBlob
    ) => {

        const formData =
            new FormData();


        formData.append(
            "file",
            audioBlob,
            "worker_voice.webm"
        );


        return request(
            "/api/v1/voice/transcribe",
            {
                method: "POST",
                body: formData,
            }
        );
    },


    // =================================================
    // MANUAL RAG
    // =================================================

    queryManuals: (
        query,
        domainFilter = null,
        topK = 5
    ) =>
        request(
            "/api/v1/manuals/query",
            {
                method: "POST",

                body: JSON.stringify({
                    query,
                    domain_filter:
                        domainFilter,
                    top_k: topK,
                }),
            }
        ),


    ingestManuals: () =>
        request(
            "/api/v1/manuals/ingest",
            {
                method: "POST",
            }
        ),


    // =================================================
    // TECHNICIAN
    // =================================================

    callTechnician: (
        message,
        toPhoneNumber,
        languageCode = "en-IN"
    ) =>
        request(
            "/api/v1/technicians/call",
            {
                method: "POST",

                body: JSON.stringify({
                    message,
                    to_phone_number:
                        toPhoneNumber,
                    language_code:
                        languageCode,
                }),
            }
        ),


    // =================================================
    // HEALTH
    // =================================================

    health: () =>
        request(
            "/api/v1/health"
        ),
};