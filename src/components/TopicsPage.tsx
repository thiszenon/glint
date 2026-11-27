
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Topic } from "../types";

export default function TopicsPage() {
    const [topics, setTopics] = useState<Topic[]>([]);
    const [name, setName] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    async function refresh() {
        try {
            setLoading(true);
            const list = await api.listTopics();
            setTopics(list);
            setError(null);
        } catch (e) {
            setError(String(e));
        } finally {
            setLoading(false);
        }
    } //end refresh

    useEffect(() => {
        refresh();
    }, []);

    async function handleAdd(e: React.FormEvent) {
        e.preventDefault();
        const trimed = name.trim();
        if (!trimed) return;
        try {
            await api.addTopic(trimed);
            setName("");
            await refresh();
        } catch (e) {
            setError(String(e));
        }
    }

    async function handleDelete(id: number) {
        try {
            await api.deleteTopic(id);
            await refresh();
        } catch (e) {
            setError(String(e));
        }
    }

    return (
        <div>
            <h1>Topics</h1>

            <form onSubmit={handleAdd}>
                <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="New topic"
                />
                <button type='submit'>Add</button>
            </form>

            {error && <p style={{color: "red"}}>{error}</p>}

            {loading ? (
                <p>Loading...</p>
            ): topics.length === 0 ? (
                <p>No topics yet.</p>
            ): (
                <ul>
                    {topics.map((t) => (
                        <li key={t.id}>
                            {t.name}{" "}
                            <button onClick={() => handleDelete(t.id)}>Delete</button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );

}