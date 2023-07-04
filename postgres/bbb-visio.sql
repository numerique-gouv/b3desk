--
-- PostgreSQL database dump
--

-- Dumped from database version 12.3 (Debian 12.3-1.pgdg100+1)
-- Dumped by pg_dump version 12.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

CREATE DATABASE bbb_visio WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.utf8' LC_CTYPE = 'en_US.utf8';

\connect bbb_visio

--
-- Data for Name: meeting; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.meeting (id, name, "attendeePW", "moderatorPW", welcome, "dialNumber", "voiceBridge", "maxParticipants", "logoutUrl", record, duration, "moderatorOnlyMessage", "autoStartRecording", "allowStartStopRecording", "webcamsOnlyForModerator", "muteOnStart", "lockSettingsDisableCam", "lockSettingsDisableMic", "allowModsToUnmuteUsers", "lockSettingsDisablePrivateChat", "lockSettingsDisablePublicChat", "lockSettingsDisableNote", logo, status, user_id) FROM stdin;
\.


--
-- Data for Name: meeting_slideshow; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.meeting_slideshow (meeting_id, slideshow_id) FROM stdin;
\.


--
-- Data for Name: slideshow; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.slideshow (id, filename, description, user_id) FROM stdin;
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."user" (id, email, given_name, family_name, presets) FROM stdin;
1	bbb-visio-user@apps.fr	BBB	User	[]
\.


--
-- Name: meeting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.meeting_id_seq', 1, false);


--
-- Name: slideshow_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.slideshow_id_seq', 1, false);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_id_seq', 1, true);


--
-- PostgreSQL database dump complete
--
