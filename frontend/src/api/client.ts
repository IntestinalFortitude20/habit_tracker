import axios from "axios";

const host = window.location.hostname;

export const api = axios.create({
  baseURL: `http://${host}:8000`,
});
