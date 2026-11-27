
import { invoke } from "@tauri-apps/api/core";
import type { Topic } from "../types";

export const api = {
    listTopics: (): Promise<Topic[]> => 
        invoke<Topic[]>("list_topics"),

    addTopic: (name: string): Promise<Topic> => 
        invoke<Topic>("add_topic", { name }),

    deleteTopic: (id: number): Promise<void> => 
        invoke<void>("delete_topic", { id }),
};