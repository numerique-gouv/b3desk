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

SET default_tablespace = '';

SET default_table_access_method = heap;

CREATE DATABASE keycloak WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.utf8' LC_CTYPE = 'en_US.utf8';

\connect keycloak

--
-- Name: admin_event_entity; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admin_event_entity (
    id character varying(36) NOT NULL,
    admin_event_time bigint,
    realm_id character varying(255),
    operation_type character varying(255),
    auth_realm_id character varying(255),
    auth_client_id character varying(255),
    auth_user_id character varying(255),
    ip_address character varying(255),
    resource_path character varying(2550),
    representation text,
    error character varying(255),
    resource_type character varying(64)
);


ALTER TABLE public.admin_event_entity OWNER TO postgres;

--
-- Name: associated_policy; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.associated_policy (
    policy_id character varying(36) NOT NULL,
    associated_policy_id character varying(36) NOT NULL
);


ALTER TABLE public.associated_policy OWNER TO postgres;

--
-- Name: authentication_execution; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.authentication_execution (
    id character varying(36) NOT NULL,
    alias character varying(255),
    authenticator character varying(36),
    realm_id character varying(36),
    flow_id character varying(36),
    requirement integer,
    priority integer,
    authenticator_flow boolean DEFAULT false NOT NULL,
    auth_flow_id character varying(36),
    auth_config character varying(36)
);


ALTER TABLE public.authentication_execution OWNER TO postgres;

--
-- Name: authentication_flow; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.authentication_flow (
    id character varying(36) NOT NULL,
    alias character varying(255),
    description character varying(255),
    realm_id character varying(36),
    provider_id character varying(36) DEFAULT 'basic-flow'::character varying NOT NULL,
    top_level boolean DEFAULT false NOT NULL,
    built_in boolean DEFAULT false NOT NULL
);


ALTER TABLE public.authentication_flow OWNER TO postgres;

--
-- Name: authenticator_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.authenticator_config (
    id character varying(36) NOT NULL,
    alias character varying(255),
    realm_id character varying(36)
);


ALTER TABLE public.authenticator_config OWNER TO postgres;

--
-- Name: authenticator_config_entry; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.authenticator_config_entry (
    authenticator_id character varying(36) NOT NULL,
    value text,
    name character varying(255) NOT NULL
);


ALTER TABLE public.authenticator_config_entry OWNER TO postgres;

--
-- Name: broker_link; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.broker_link (
    identity_provider character varying(255) NOT NULL,
    storage_provider_id character varying(255),
    realm_id character varying(36) NOT NULL,
    broker_user_id character varying(255),
    broker_username character varying(255),
    token text,
    user_id character varying(255) NOT NULL
);


ALTER TABLE public.broker_link OWNER TO postgres;

--
-- Name: client; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client (
    id character varying(36) NOT NULL,
    enabled boolean DEFAULT false NOT NULL,
    full_scope_allowed boolean DEFAULT false NOT NULL,
    client_id character varying(255),
    not_before integer,
    public_client boolean DEFAULT false NOT NULL,
    secret character varying(255),
    base_url character varying(255),
    bearer_only boolean DEFAULT false NOT NULL,
    management_url character varying(255),
    surrogate_auth_required boolean DEFAULT false NOT NULL,
    realm_id character varying(36),
    protocol character varying(255),
    node_rereg_timeout integer DEFAULT 0,
    frontchannel_logout boolean DEFAULT false NOT NULL,
    consent_required boolean DEFAULT false NOT NULL,
    name character varying(255),
    service_accounts_enabled boolean DEFAULT false NOT NULL,
    client_authenticator_type character varying(255),
    root_url character varying(255),
    description character varying(255),
    registration_token character varying(255),
    standard_flow_enabled boolean DEFAULT true NOT NULL,
    implicit_flow_enabled boolean DEFAULT false NOT NULL,
    direct_access_grants_enabled boolean DEFAULT false NOT NULL,
    always_display_in_console boolean DEFAULT false NOT NULL
);


ALTER TABLE public.client OWNER TO postgres;

--
-- Name: client_attributes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_attributes (
    client_id character varying(36) NOT NULL,
    value character varying(4000),
    name character varying(255) NOT NULL
);


ALTER TABLE public.client_attributes OWNER TO postgres;

--
-- Name: client_auth_flow_bindings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_auth_flow_bindings (
    client_id character varying(36) NOT NULL,
    flow_id character varying(36),
    binding_name character varying(255) NOT NULL
);


ALTER TABLE public.client_auth_flow_bindings OWNER TO postgres;

--
-- Name: client_default_roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_default_roles (
    client_id character varying(36) NOT NULL,
    role_id character varying(36) NOT NULL
);


ALTER TABLE public.client_default_roles OWNER TO postgres;

--
-- Name: client_initial_access; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_initial_access (
    id character varying(36) NOT NULL,
    realm_id character varying(36) NOT NULL,
    "timestamp" integer,
    expiration integer,
    count integer,
    remaining_count integer
);


ALTER TABLE public.client_initial_access OWNER TO postgres;

--
-- Name: client_node_registrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_node_registrations (
    client_id character varying(36) NOT NULL,
    value integer,
    name character varying(255) NOT NULL
);


ALTER TABLE public.client_node_registrations OWNER TO postgres;

--
-- Name: client_scope; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_scope (
    id character varying(36) NOT NULL,
    name character varying(255),
    realm_id character varying(36),
    description character varying(255),
    protocol character varying(255)
);


ALTER TABLE public.client_scope OWNER TO postgres;

--
-- Name: client_scope_attributes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_scope_attributes (
    scope_id character varying(36) NOT NULL,
    value character varying(2048),
    name character varying(255) NOT NULL
);


ALTER TABLE public.client_scope_attributes OWNER TO postgres;

--
-- Name: client_scope_client; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_scope_client (
    client_id character varying(36) NOT NULL,
    scope_id character varying(36) NOT NULL,
    default_scope boolean DEFAULT false NOT NULL
);


ALTER TABLE public.client_scope_client OWNER TO postgres;

--
-- Name: client_scope_role_mapping; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_scope_role_mapping (
    scope_id character varying(36) NOT NULL,
    role_id character varying(36) NOT NULL
);


ALTER TABLE public.client_scope_role_mapping OWNER TO postgres;

--
-- Name: client_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_session (
    id character varying(36) NOT NULL,
    client_id character varying(36),
    redirect_uri character varying(255),
    state character varying(255),
    "timestamp" integer,
    session_id character varying(36),
    auth_method character varying(255),
    realm_id character varying(255),
    auth_user_id character varying(36),
    current_action character varying(36)
);


ALTER TABLE public.client_session OWNER TO postgres;

--
-- Name: client_session_auth_status; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_session_auth_status (
    authenticator character varying(36) NOT NULL,
    status integer,
    client_session character varying(36) NOT NULL
);


ALTER TABLE public.client_session_auth_status OWNER TO postgres;

--
-- Name: client_session_note; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_session_note (
    name character varying(255) NOT NULL,
    value character varying(255),
    client_session character varying(36) NOT NULL
);


ALTER TABLE public.client_session_note OWNER TO postgres;

--
-- Name: client_session_prot_mapper; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_session_prot_mapper (
    protocol_mapper_id character varying(36) NOT NULL,
    client_session character varying(36) NOT NULL
);


ALTER TABLE public.client_session_prot_mapper OWNER TO postgres;

--
-- Name: client_session_role; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_session_role (
    role_id character varying(255) NOT NULL,
    client_session character varying(36) NOT NULL
);


ALTER TABLE public.client_session_role OWNER TO postgres;

--
-- Name: client_user_session_note; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_user_session_note (
    name character varying(255) NOT NULL,
    value character varying(2048),
    client_session character varying(36) NOT NULL
);


ALTER TABLE public.client_user_session_note OWNER TO postgres;

--
-- Name: component; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.component (
    id character varying(36) NOT NULL,
    name character varying(255),
    parent_id character varying(36),
    provider_id character varying(36),
    provider_type character varying(255),
    realm_id character varying(36),
    sub_type character varying(255)
);


ALTER TABLE public.component OWNER TO postgres;

--
-- Name: component_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.component_config (
    id character varying(36) NOT NULL,
    component_id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    value character varying(4000)
);


ALTER TABLE public.component_config OWNER TO postgres;

--
-- Name: composite_role; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.composite_role (
    composite character varying(36) NOT NULL,
    child_role character varying(36) NOT NULL
);


ALTER TABLE public.composite_role OWNER TO postgres;

--
-- Name: credential; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.credential (
    id character varying(36) NOT NULL,
    salt bytea,
    type character varying(255),
    user_id character varying(36),
    created_date bigint,
    user_label character varying(255),
    secret_data text,
    credential_data text,
    priority integer
);


ALTER TABLE public.credential OWNER TO postgres;

--
-- Name: databasechangelog; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.databasechangelog (
    id character varying(255) NOT NULL,
    author character varying(255) NOT NULL,
    filename character varying(255) NOT NULL,
    dateexecuted timestamp without time zone NOT NULL,
    orderexecuted integer NOT NULL,
    exectype character varying(10) NOT NULL,
    md5sum character varying(35),
    description character varying(255),
    comments character varying(255),
    tag character varying(255),
    liquibase character varying(20),
    contexts character varying(255),
    labels character varying(255),
    deployment_id character varying(10)
);


ALTER TABLE public.databasechangelog OWNER TO postgres;

--
-- Name: databasechangeloglock; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.databasechangeloglock (
    id integer NOT NULL,
    locked boolean NOT NULL,
    lockgranted timestamp without time zone,
    lockedby character varying(255)
);


ALTER TABLE public.databasechangeloglock OWNER TO postgres;

--
-- Name: default_client_scope; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.default_client_scope (
    realm_id character varying(36) NOT NULL,
    scope_id character varying(36) NOT NULL,
    default_scope boolean DEFAULT false NOT NULL
);


ALTER TABLE public.default_client_scope OWNER TO postgres;

--
-- Name: event_entity; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.event_entity (
    id character varying(36) NOT NULL,
    client_id character varying(255),
    details_json character varying(2550),
    error character varying(255),
    ip_address character varying(255),
    realm_id character varying(255),
    session_id character varying(255),
    event_time bigint,
    type character varying(255),
    user_id character varying(255)
);


ALTER TABLE public.event_entity OWNER TO postgres;

--
-- Name: fed_user_attribute; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fed_user_attribute (
    id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    user_id character varying(255) NOT NULL,
    realm_id character varying(36) NOT NULL,
    storage_provider_id character varying(36),
    value character varying(2024)
);


ALTER TABLE public.fed_user_attribute OWNER TO postgres;

--
-- Name: fed_user_consent; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fed_user_consent (
    id character varying(36) NOT NULL,
    client_id character varying(255),
    user_id character varying(255) NOT NULL,
    realm_id character varying(36) NOT NULL,
    storage_provider_id character varying(36),
    created_date bigint,
    last_updated_date bigint,
    client_storage_provider character varying(36),
    external_client_id character varying(255)
);


ALTER TABLE public.fed_user_consent OWNER TO postgres;

--
-- Name: fed_user_consent_cl_scope; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fed_user_consent_cl_scope (
    user_consent_id character varying(36) NOT NULL,
    scope_id character varying(36) NOT NULL
);


ALTER TABLE public.fed_user_consent_cl_scope OWNER TO postgres;

--
-- Name: fed_user_credential; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fed_user_credential (
    id character varying(36) NOT NULL,
    salt bytea,
    type character varying(255),
    created_date bigint,
    user_id character varying(255) NOT NULL,
    realm_id character varying(36) NOT NULL,
    storage_provider_id character varying(36),
    user_label character varying(255),
    secret_data text,
    credential_data text,
    priority integer
);


ALTER TABLE public.fed_user_credential OWNER TO postgres;

--
-- Name: fed_user_group_membership; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fed_user_group_membership (
    group_id character varying(36) NOT NULL,
    user_id character varying(255) NOT NULL,
    realm_id character varying(36) NOT NULL,
    storage_provider_id character varying(36)
);


ALTER TABLE public.fed_user_group_membership OWNER TO postgres;

--
-- Name: fed_user_required_action; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fed_user_required_action (
    required_action character varying(255) DEFAULT ' '::character varying NOT NULL,
    user_id character varying(255) NOT NULL,
    realm_id character varying(36) NOT NULL,
    storage_provider_id character varying(36)
);


ALTER TABLE public.fed_user_required_action OWNER TO postgres;

--
-- Name: fed_user_role_mapping; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fed_user_role_mapping (
    role_id character varying(36) NOT NULL,
    user_id character varying(255) NOT NULL,
    realm_id character varying(36) NOT NULL,
    storage_provider_id character varying(36)
);


ALTER TABLE public.fed_user_role_mapping OWNER TO postgres;

--
-- Name: federated_identity; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.federated_identity (
    identity_provider character varying(255) NOT NULL,
    realm_id character varying(36),
    federated_user_id character varying(255),
    federated_username character varying(255),
    token text,
    user_id character varying(36) NOT NULL
);


ALTER TABLE public.federated_identity OWNER TO postgres;

--
-- Name: federated_user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.federated_user (
    id character varying(255) NOT NULL,
    storage_provider_id character varying(255),
    realm_id character varying(36) NOT NULL
);


ALTER TABLE public.federated_user OWNER TO postgres;

--
-- Name: group_attribute; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.group_attribute (
    id character varying(36) DEFAULT 'sybase-needs-something-here'::character varying NOT NULL,
    name character varying(255) NOT NULL,
    value character varying(255),
    group_id character varying(36) NOT NULL
);


ALTER TABLE public.group_attribute OWNER TO postgres;

--
-- Name: group_role_mapping; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.group_role_mapping (
    role_id character varying(36) NOT NULL,
    group_id character varying(36) NOT NULL
);


ALTER TABLE public.group_role_mapping OWNER TO postgres;

--
-- Name: identity_provider; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.identity_provider (
    internal_id character varying(36) NOT NULL,
    enabled boolean DEFAULT false NOT NULL,
    provider_alias character varying(255),
    provider_id character varying(255),
    store_token boolean DEFAULT false NOT NULL,
    authenticate_by_default boolean DEFAULT false NOT NULL,
    realm_id character varying(36),
    add_token_role boolean DEFAULT true NOT NULL,
    trust_email boolean DEFAULT false NOT NULL,
    first_broker_login_flow_id character varying(36),
    post_broker_login_flow_id character varying(36),
    provider_display_name character varying(255),
    link_only boolean DEFAULT false NOT NULL
);


ALTER TABLE public.identity_provider OWNER TO postgres;

--
-- Name: identity_provider_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.identity_provider_config (
    identity_provider_id character varying(36) NOT NULL,
    value text,
    name character varying(255) NOT NULL
);


ALTER TABLE public.identity_provider_config OWNER TO postgres;

--
-- Name: identity_provider_mapper; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.identity_provider_mapper (
    id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    idp_alias character varying(255) NOT NULL,
    idp_mapper_name character varying(255) NOT NULL,
    realm_id character varying(36) NOT NULL
);


ALTER TABLE public.identity_provider_mapper OWNER TO postgres;

--
-- Name: idp_mapper_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.idp_mapper_config (
    idp_mapper_id character varying(36) NOT NULL,
    value text,
    name character varying(255) NOT NULL
);


ALTER TABLE public.idp_mapper_config OWNER TO postgres;

--
-- Name: keycloak_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.keycloak_group (
    id character varying(36) NOT NULL,
    name character varying(255),
    parent_group character varying(36) NOT NULL,
    realm_id character varying(36)
);


ALTER TABLE public.keycloak_group OWNER TO postgres;

--
-- Name: keycloak_role; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.keycloak_role (
    id character varying(36) NOT NULL,
    client_realm_constraint character varying(255),
    client_role boolean DEFAULT false NOT NULL,
    description character varying(255),
    name character varying(255),
    realm_id character varying(255),
    client character varying(36),
    realm character varying(36)
);


ALTER TABLE public.keycloak_role OWNER TO postgres;

--
-- Name: migration_model; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.migration_model (
    id character varying(36) NOT NULL,
    version character varying(36),
    update_time bigint DEFAULT 0 NOT NULL
);


ALTER TABLE public.migration_model OWNER TO postgres;

--
-- Name: offline_client_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.offline_client_session (
    user_session_id character varying(36) NOT NULL,
    client_id character varying(255) NOT NULL,
    offline_flag character varying(4) NOT NULL,
    "timestamp" integer,
    data text,
    client_storage_provider character varying(36) DEFAULT 'local'::character varying NOT NULL,
    external_client_id character varying(255) DEFAULT 'local'::character varying NOT NULL
);


ALTER TABLE public.offline_client_session OWNER TO postgres;

--
-- Name: offline_user_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.offline_user_session (
    user_session_id character varying(36) NOT NULL,
    user_id character varying(255) NOT NULL,
    realm_id character varying(36) NOT NULL,
    created_on integer NOT NULL,
    offline_flag character varying(4) NOT NULL,
    data text,
    last_session_refresh integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.offline_user_session OWNER TO postgres;

--
-- Name: policy_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.policy_config (
    policy_id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    value text
);


ALTER TABLE public.policy_config OWNER TO postgres;

--
-- Name: protocol_mapper; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.protocol_mapper (
    id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    protocol character varying(255) NOT NULL,
    protocol_mapper_name character varying(255) NOT NULL,
    client_id character varying(36),
    client_scope_id character varying(36)
);


ALTER TABLE public.protocol_mapper OWNER TO postgres;

--
-- Name: protocol_mapper_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.protocol_mapper_config (
    protocol_mapper_id character varying(36) NOT NULL,
    value text,
    name character varying(255) NOT NULL
);


ALTER TABLE public.protocol_mapper_config OWNER TO postgres;

--
-- Name: realm; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.realm (
    id character varying(36) NOT NULL,
    access_code_lifespan integer,
    user_action_lifespan integer,
    access_token_lifespan integer,
    account_theme character varying(255),
    admin_theme character varying(255),
    email_theme character varying(255),
    enabled boolean DEFAULT false NOT NULL,
    events_enabled boolean DEFAULT false NOT NULL,
    events_expiration bigint,
    login_theme character varying(255),
    name character varying(255),
    not_before integer,
    password_policy character varying(2550),
    registration_allowed boolean DEFAULT false NOT NULL,
    remember_me boolean DEFAULT false NOT NULL,
    reset_password_allowed boolean DEFAULT false NOT NULL,
    social boolean DEFAULT false NOT NULL,
    ssl_required character varying(255),
    sso_idle_timeout integer,
    sso_max_lifespan integer,
    update_profile_on_soc_login boolean DEFAULT false NOT NULL,
    verify_email boolean DEFAULT false NOT NULL,
    master_admin_client character varying(36),
    login_lifespan integer,
    internationalization_enabled boolean DEFAULT false NOT NULL,
    default_locale character varying(255),
    reg_email_as_username boolean DEFAULT false NOT NULL,
    admin_events_enabled boolean DEFAULT false NOT NULL,
    admin_events_details_enabled boolean DEFAULT false NOT NULL,
    edit_username_allowed boolean DEFAULT false NOT NULL,
    otp_policy_counter integer DEFAULT 0,
    otp_policy_window integer DEFAULT 1,
    otp_policy_period integer DEFAULT 30,
    otp_policy_digits integer DEFAULT 6,
    otp_policy_alg character varying(36) DEFAULT 'HmacSHA1'::character varying,
    otp_policy_type character varying(36) DEFAULT 'totp'::character varying,
    browser_flow character varying(36),
    registration_flow character varying(36),
    direct_grant_flow character varying(36),
    reset_credentials_flow character varying(36),
    client_auth_flow character varying(36),
    offline_session_idle_timeout integer DEFAULT 0,
    revoke_refresh_token boolean DEFAULT false NOT NULL,
    access_token_life_implicit integer DEFAULT 0,
    login_with_email_allowed boolean DEFAULT true NOT NULL,
    duplicate_emails_allowed boolean DEFAULT false NOT NULL,
    docker_auth_flow character varying(36),
    refresh_token_max_reuse integer DEFAULT 0,
    allow_user_managed_access boolean DEFAULT false NOT NULL,
    sso_max_lifespan_remember_me integer DEFAULT 0 NOT NULL,
    sso_idle_timeout_remember_me integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.realm OWNER TO postgres;

--
-- Name: realm_attribute; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.realm_attribute (
    name character varying(255) NOT NULL,
    value character varying(255),
    realm_id character varying(36) NOT NULL
);


ALTER TABLE public.realm_attribute OWNER TO postgres;

--
-- Name: realm_default_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.realm_default_groups (
    realm_id character varying(36) NOT NULL,
    group_id character varying(36) NOT NULL
);


ALTER TABLE public.realm_default_groups OWNER TO postgres;

--
-- Name: realm_default_roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.realm_default_roles (
    realm_id character varying(36) NOT NULL,
    role_id character varying(36) NOT NULL
);


ALTER TABLE public.realm_default_roles OWNER TO postgres;

--
-- Name: realm_enabled_event_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.realm_enabled_event_types (
    realm_id character varying(36) NOT NULL,
    value character varying(255) NOT NULL
);


ALTER TABLE public.realm_enabled_event_types OWNER TO postgres;

--
-- Name: realm_events_listeners; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.realm_events_listeners (
    realm_id character varying(36) NOT NULL,
    value character varying(255) NOT NULL
);


ALTER TABLE public.realm_events_listeners OWNER TO postgres;

--
-- Name: realm_required_credential; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.realm_required_credential (
    type character varying(255) NOT NULL,
    form_label character varying(255),
    input boolean DEFAULT false NOT NULL,
    secret boolean DEFAULT false NOT NULL,
    realm_id character varying(36) NOT NULL
);


ALTER TABLE public.realm_required_credential OWNER TO postgres;

--
-- Name: realm_smtp_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.realm_smtp_config (
    realm_id character varying(36) NOT NULL,
    value character varying(255),
    name character varying(255) NOT NULL
);


ALTER TABLE public.realm_smtp_config OWNER TO postgres;

--
-- Name: realm_supported_locales; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.realm_supported_locales (
    realm_id character varying(36) NOT NULL,
    value character varying(255) NOT NULL
);


ALTER TABLE public.realm_supported_locales OWNER TO postgres;

--
-- Name: redirect_uris; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.redirect_uris (
    client_id character varying(36) NOT NULL,
    value character varying(255) NOT NULL
);


ALTER TABLE public.redirect_uris OWNER TO postgres;

--
-- Name: required_action_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.required_action_config (
    required_action_id character varying(36) NOT NULL,
    value text,
    name character varying(255) NOT NULL
);


ALTER TABLE public.required_action_config OWNER TO postgres;

--
-- Name: required_action_provider; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.required_action_provider (
    id character varying(36) NOT NULL,
    alias character varying(255),
    name character varying(255),
    realm_id character varying(36),
    enabled boolean DEFAULT false NOT NULL,
    default_action boolean DEFAULT false NOT NULL,
    provider_id character varying(255),
    priority integer
);


ALTER TABLE public.required_action_provider OWNER TO postgres;

--
-- Name: resource_attribute; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resource_attribute (
    id character varying(36) DEFAULT 'sybase-needs-something-here'::character varying NOT NULL,
    name character varying(255) NOT NULL,
    value character varying(255),
    resource_id character varying(36) NOT NULL
);


ALTER TABLE public.resource_attribute OWNER TO postgres;

--
-- Name: resource_policy; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resource_policy (
    resource_id character varying(36) NOT NULL,
    policy_id character varying(36) NOT NULL
);


ALTER TABLE public.resource_policy OWNER TO postgres;

--
-- Name: resource_scope; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resource_scope (
    resource_id character varying(36) NOT NULL,
    scope_id character varying(36) NOT NULL
);


ALTER TABLE public.resource_scope OWNER TO postgres;

--
-- Name: resource_server; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resource_server (
    id character varying(36) NOT NULL,
    allow_rs_remote_mgmt boolean DEFAULT false NOT NULL,
    policy_enforce_mode character varying(15) NOT NULL,
    decision_strategy smallint DEFAULT 1 NOT NULL
);


ALTER TABLE public.resource_server OWNER TO postgres;

--
-- Name: resource_server_perm_ticket; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resource_server_perm_ticket (
    id character varying(36) NOT NULL,
    owner character varying(255) NOT NULL,
    requester character varying(255) NOT NULL,
    created_timestamp bigint NOT NULL,
    granted_timestamp bigint,
    resource_id character varying(36) NOT NULL,
    scope_id character varying(36),
    resource_server_id character varying(36) NOT NULL,
    policy_id character varying(36)
);


ALTER TABLE public.resource_server_perm_ticket OWNER TO postgres;

--
-- Name: resource_server_policy; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resource_server_policy (
    id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(255),
    type character varying(255) NOT NULL,
    decision_strategy character varying(20),
    logic character varying(20),
    resource_server_id character varying(36) NOT NULL,
    owner character varying(255)
);


ALTER TABLE public.resource_server_policy OWNER TO postgres;

--
-- Name: resource_server_resource; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resource_server_resource (
    id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    type character varying(255),
    icon_uri character varying(255),
    owner character varying(255) NOT NULL,
    resource_server_id character varying(36) NOT NULL,
    owner_managed_access boolean DEFAULT false NOT NULL,
    display_name character varying(255)
);


ALTER TABLE public.resource_server_resource OWNER TO postgres;

--
-- Name: resource_server_scope; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resource_server_scope (
    id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    icon_uri character varying(255),
    resource_server_id character varying(36) NOT NULL,
    display_name character varying(255)
);


ALTER TABLE public.resource_server_scope OWNER TO postgres;

--
-- Name: resource_uris; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resource_uris (
    resource_id character varying(36) NOT NULL,
    value character varying(255) NOT NULL
);


ALTER TABLE public.resource_uris OWNER TO postgres;

--
-- Name: role_attribute; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.role_attribute (
    id character varying(36) NOT NULL,
    role_id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    value character varying(255)
);


ALTER TABLE public.role_attribute OWNER TO postgres;

--
-- Name: scope_mapping; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scope_mapping (
    client_id character varying(36) NOT NULL,
    role_id character varying(36) NOT NULL
);


ALTER TABLE public.scope_mapping OWNER TO postgres;

--
-- Name: scope_policy; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scope_policy (
    scope_id character varying(36) NOT NULL,
    policy_id character varying(36) NOT NULL
);


ALTER TABLE public.scope_policy OWNER TO postgres;

--
-- Name: user_attribute; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_attribute (
    name character varying(255) NOT NULL,
    value character varying(255),
    user_id character varying(36) NOT NULL,
    id character varying(36) DEFAULT 'sybase-needs-something-here'::character varying NOT NULL
);


ALTER TABLE public.user_attribute OWNER TO postgres;

--
-- Name: user_consent; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_consent (
    id character varying(36) NOT NULL,
    client_id character varying(255),
    user_id character varying(36) NOT NULL,
    created_date bigint,
    last_updated_date bigint,
    client_storage_provider character varying(36),
    external_client_id character varying(255)
);


ALTER TABLE public.user_consent OWNER TO postgres;

--
-- Name: user_consent_client_scope; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_consent_client_scope (
    user_consent_id character varying(36) NOT NULL,
    scope_id character varying(36) NOT NULL
);


ALTER TABLE public.user_consent_client_scope OWNER TO postgres;

--
-- Name: user_entity; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_entity (
    id character varying(36) NOT NULL,
    email character varying(255),
    email_constraint character varying(255),
    email_verified boolean DEFAULT false NOT NULL,
    enabled boolean DEFAULT false NOT NULL,
    federation_link character varying(255),
    first_name character varying(255),
    last_name character varying(255),
    realm_id character varying(255),
    username character varying(255),
    created_timestamp bigint,
    service_account_client_link character varying(255),
    not_before integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.user_entity OWNER TO postgres;

--
-- Name: user_federation_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_federation_config (
    user_federation_provider_id character varying(36) NOT NULL,
    value character varying(255),
    name character varying(255) NOT NULL
);


ALTER TABLE public.user_federation_config OWNER TO postgres;

--
-- Name: user_federation_mapper; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_federation_mapper (
    id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    federation_provider_id character varying(36) NOT NULL,
    federation_mapper_type character varying(255) NOT NULL,
    realm_id character varying(36) NOT NULL
);


ALTER TABLE public.user_federation_mapper OWNER TO postgres;

--
-- Name: user_federation_mapper_config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_federation_mapper_config (
    user_federation_mapper_id character varying(36) NOT NULL,
    value character varying(255),
    name character varying(255) NOT NULL
);


ALTER TABLE public.user_federation_mapper_config OWNER TO postgres;

--
-- Name: user_federation_provider; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_federation_provider (
    id character varying(36) NOT NULL,
    changed_sync_period integer,
    display_name character varying(255),
    full_sync_period integer,
    last_sync integer,
    priority integer,
    provider_name character varying(255),
    realm_id character varying(36)
);


ALTER TABLE public.user_federation_provider OWNER TO postgres;

--
-- Name: user_group_membership; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_group_membership (
    group_id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL
);


ALTER TABLE public.user_group_membership OWNER TO postgres;

--
-- Name: user_required_action; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_required_action (
    user_id character varying(36) NOT NULL,
    required_action character varying(255) DEFAULT ' '::character varying NOT NULL
);


ALTER TABLE public.user_required_action OWNER TO postgres;

--
-- Name: user_role_mapping; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_role_mapping (
    role_id character varying(255) NOT NULL,
    user_id character varying(36) NOT NULL
);


ALTER TABLE public.user_role_mapping OWNER TO postgres;

--
-- Name: user_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_session (
    id character varying(36) NOT NULL,
    auth_method character varying(255),
    ip_address character varying(255),
    last_session_refresh integer,
    login_username character varying(255),
    realm_id character varying(255),
    remember_me boolean DEFAULT false NOT NULL,
    started integer,
    user_id character varying(255),
    user_session_state integer,
    broker_session_id character varying(255),
    broker_user_id character varying(255)
);


ALTER TABLE public.user_session OWNER TO postgres;

--
-- Name: user_session_note; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_session_note (
    user_session character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    value character varying(2048)
);


ALTER TABLE public.user_session_note OWNER TO postgres;

--
-- Name: username_login_failure; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.username_login_failure (
    realm_id character varying(36) NOT NULL,
    username character varying(255) NOT NULL,
    failed_login_not_before integer,
    last_failure bigint,
    last_ip_failure character varying(255),
    num_failures integer
);


ALTER TABLE public.username_login_failure OWNER TO postgres;

--
-- Name: web_origins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.web_origins (
    client_id character varying(36) NOT NULL,
    value character varying(255) NOT NULL
);


ALTER TABLE public.web_origins OWNER TO postgres;

--
-- Data for Name: admin_event_entity; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.admin_event_entity (id, admin_event_time, realm_id, operation_type, auth_realm_id, auth_client_id, auth_user_id, ip_address, resource_path, representation, error, resource_type) FROM stdin;
\.


--
-- Data for Name: associated_policy; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.associated_policy (policy_id, associated_policy_id) FROM stdin;
\.


--
-- Data for Name: authentication_execution; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.authentication_execution (id, alias, authenticator, realm_id, flow_id, requirement, priority, authenticator_flow, auth_flow_id, auth_config) FROM stdin;
79a0c485-59cf-4294-b15b-9a74d1af5951	\N	auth-cookie	master	671696be-a848-4d42-b76b-12256aeda5bf	2	10	f	\N	\N
03948139-08ba-4f2f-a042-a836138582da	\N	auth-spnego	master	671696be-a848-4d42-b76b-12256aeda5bf	3	20	f	\N	\N
c0a74ef3-f981-4b4c-a9b7-9554d0069e23	\N	identity-provider-redirector	master	671696be-a848-4d42-b76b-12256aeda5bf	2	25	f	\N	\N
76bdc20c-b67a-4935-8da1-c51e7cb666a5	\N	\N	master	671696be-a848-4d42-b76b-12256aeda5bf	2	30	t	f9fe24ad-c52a-4435-a505-1344558430db	\N
8421123c-7690-4c5c-b20e-113dd7a96c9a	\N	auth-username-password-form	master	f9fe24ad-c52a-4435-a505-1344558430db	0	10	f	\N	\N
66da5208-cdbf-4fe5-a8a1-302504cdd3b6	\N	\N	master	f9fe24ad-c52a-4435-a505-1344558430db	1	20	t	5496fb50-3ae6-4867-802f-ea10ff9bb3c3	\N
830f2c5c-a2c2-4b10-8445-21534395ad69	\N	conditional-user-configured	master	5496fb50-3ae6-4867-802f-ea10ff9bb3c3	0	10	f	\N	\N
5a462ac0-a8e1-4bd6-b16e-87895210dbfb	\N	auth-otp-form	master	5496fb50-3ae6-4867-802f-ea10ff9bb3c3	0	20	f	\N	\N
492126f3-fa45-4057-b53f-d35c423311a3	\N	direct-grant-validate-username	master	6c5aa605-ea06-4926-816d-63d756e9fcc5	0	10	f	\N	\N
4568b749-63bb-44d8-a640-c266a1d63226	\N	direct-grant-validate-password	master	6c5aa605-ea06-4926-816d-63d756e9fcc5	0	20	f	\N	\N
55c06d40-526b-4973-a21c-138873fef2c3	\N	\N	master	6c5aa605-ea06-4926-816d-63d756e9fcc5	1	30	t	0930751d-69b3-497d-acc9-6b25e3cbe524	\N
a36e91f7-4901-4a89-a2d0-3dab05845389	\N	conditional-user-configured	master	0930751d-69b3-497d-acc9-6b25e3cbe524	0	10	f	\N	\N
b1223300-5c9b-4c15-8d6a-bf19f9cb5aa4	\N	direct-grant-validate-otp	master	0930751d-69b3-497d-acc9-6b25e3cbe524	0	20	f	\N	\N
ea3dec2f-e41e-41d4-aaf8-49cbe472db5d	\N	registration-page-form	master	833f05e8-0902-4f4c-a2a7-154e3f7619d6	0	10	t	9cc1b3ac-ff29-4fd5-baf8-083222695e7a	\N
5b562f26-e9e7-4ffc-8a70-78b4361a0cd6	\N	registration-user-creation	master	9cc1b3ac-ff29-4fd5-baf8-083222695e7a	0	20	f	\N	\N
67e97f5b-90e2-426f-b284-2cd52f68391d	\N	registration-profile-action	master	9cc1b3ac-ff29-4fd5-baf8-083222695e7a	0	40	f	\N	\N
cdf7fa67-0f32-4902-aefe-436eb4161761	\N	registration-password-action	master	9cc1b3ac-ff29-4fd5-baf8-083222695e7a	0	50	f	\N	\N
e2bec4ed-215e-458d-ab5e-e250ee56f34e	\N	registration-recaptcha-action	master	9cc1b3ac-ff29-4fd5-baf8-083222695e7a	3	60	f	\N	\N
e41c9670-0527-400a-bf68-3748aaf98446	\N	reset-credentials-choose-user	master	3374da34-b4fd-4870-91dc-110f78513d18	0	10	f	\N	\N
9dc28be3-041d-476e-8431-91b32214205a	\N	reset-credential-email	master	3374da34-b4fd-4870-91dc-110f78513d18	0	20	f	\N	\N
131819fa-12f4-4bb3-b5e5-f5afcb7e80a5	\N	reset-password	master	3374da34-b4fd-4870-91dc-110f78513d18	0	30	f	\N	\N
2ca2a069-e4a8-44a0-91c2-59fbf872de0f	\N	\N	master	3374da34-b4fd-4870-91dc-110f78513d18	1	40	t	0071d85e-1122-4941-b647-04bd94b80903	\N
59b86145-8fc1-4131-9316-aa6f174895f1	\N	conditional-user-configured	master	0071d85e-1122-4941-b647-04bd94b80903	0	10	f	\N	\N
4fb21a83-2688-4d73-bc40-6bea56b57b28	\N	reset-otp	master	0071d85e-1122-4941-b647-04bd94b80903	0	20	f	\N	\N
d9b6ecb4-bc98-4de2-9399-f81ac2c1c87e	\N	client-secret	master	2600c0ce-4c95-46aa-a62c-32cd8af0c837	2	10	f	\N	\N
4c074201-4bc9-46b6-8682-a55409b4931e	\N	client-jwt	master	2600c0ce-4c95-46aa-a62c-32cd8af0c837	2	20	f	\N	\N
d8838981-17d1-458c-8797-ad75c916620e	\N	client-secret-jwt	master	2600c0ce-4c95-46aa-a62c-32cd8af0c837	2	30	f	\N	\N
7506d6ad-447e-4084-a922-5e62f647a8e1	\N	client-x509	master	2600c0ce-4c95-46aa-a62c-32cd8af0c837	2	40	f	\N	\N
4e8ee2b2-8639-4978-911f-c83f86ec11d3	\N	idp-review-profile	master	4d08f1c0-a049-4581-90db-b3545b1f2afa	0	10	f	\N	77387157-bee1-4fbf-ab5b-cc773b54c3a1
ecf80d03-b3ea-4c7f-ae8e-119573d60bc1	\N	\N	master	4d08f1c0-a049-4581-90db-b3545b1f2afa	0	20	t	8afa7bbb-0c3c-481c-995a-d4c9bb53d8dc	\N
ca38bfa2-4bd6-4878-ab78-1abd7245f9d9	\N	idp-create-user-if-unique	master	8afa7bbb-0c3c-481c-995a-d4c9bb53d8dc	2	10	f	\N	d013cd7f-1246-4e13-a7bf-a8babfad367f
8ac06551-1105-4822-b06e-4d03e670da7a	\N	\N	master	8afa7bbb-0c3c-481c-995a-d4c9bb53d8dc	2	20	t	75654d9d-278b-4e86-96ad-b0593f23d7a6	\N
055b4dca-f79f-4071-93f7-2cff3b1ba04d	\N	idp-confirm-link	master	75654d9d-278b-4e86-96ad-b0593f23d7a6	0	10	f	\N	\N
a94ec02d-4f16-4219-b2bc-39039090cd0d	\N	\N	master	75654d9d-278b-4e86-96ad-b0593f23d7a6	0	20	t	f3b0a0f8-6aba-40ac-8bf3-a83606a99ee5	\N
d223cd5a-db08-4488-ae75-8971c3703ff1	\N	idp-email-verification	master	f3b0a0f8-6aba-40ac-8bf3-a83606a99ee5	2	10	f	\N	\N
c0d86034-73c1-465d-96ef-1d345ca9d46f	\N	\N	master	f3b0a0f8-6aba-40ac-8bf3-a83606a99ee5	2	20	t	b12fcbdc-c438-4af0-919d-f48a5d85b7a2	\N
2bf1df1f-33ed-40ec-b100-97d921b2bb59	\N	idp-username-password-form	master	b12fcbdc-c438-4af0-919d-f48a5d85b7a2	0	10	f	\N	\N
bfbedbac-782f-4435-935b-2c3bc5c1b96a	\N	\N	master	b12fcbdc-c438-4af0-919d-f48a5d85b7a2	1	20	t	7e9e5da4-1318-4aae-827b-61c7f2205a52	\N
50945ab4-0ade-40f6-a01b-d4abd74dc4ad	\N	conditional-user-configured	master	7e9e5da4-1318-4aae-827b-61c7f2205a52	0	10	f	\N	\N
53fb3334-0ac9-47f5-9965-089b6b7741a2	\N	auth-otp-form	master	7e9e5da4-1318-4aae-827b-61c7f2205a52	0	20	f	\N	\N
53fcf075-b09f-41c4-8ea9-78e5f23261a1	\N	http-basic-authenticator	master	381652e9-b0d3-4595-bc7d-ce12f6c922f0	0	10	f	\N	\N
7a7d9c9c-09a1-430c-8310-9ed125c2afc7	\N	docker-http-basic-authenticator	master	43bbde40-8833-4e98-82ae-a1c85d4295bd	0	10	f	\N	\N
fc0c2ec2-f529-4706-bcff-5698b65a36b4	\N	no-cookie-redirect	master	a0ae80a5-2c54-4988-ad28-8c5d1e26eb83	0	10	f	\N	\N
0bcfe0b3-919b-4bd5-b84c-3e58a8d3b1de	\N	\N	master	a0ae80a5-2c54-4988-ad28-8c5d1e26eb83	0	20	t	2b7dece4-c69e-4873-bc2d-36e896914d24	\N
b5f5cfcd-f729-40b7-9e65-7b6c56113860	\N	basic-auth	master	2b7dece4-c69e-4873-bc2d-36e896914d24	0	10	f	\N	\N
86bc58c7-705a-444c-abf2-2a83877e75e5	\N	basic-auth-otp	master	2b7dece4-c69e-4873-bc2d-36e896914d24	3	20	f	\N	\N
445cd29a-b219-47cc-9ee2-f23d94966cd8	\N	auth-spnego	master	2b7dece4-c69e-4873-bc2d-36e896914d24	3	30	f	\N	\N
8d011f59-ef83-4860-be9c-c2c0d068388c	\N	auth-cookie	apps	d552f890-1b2d-4a78-aa6a-0394e5d52a4b	2	10	f	\N	\N
f6f8b67a-fd09-4c9b-9f4f-58d0992f0187	\N	auth-spnego	apps	d552f890-1b2d-4a78-aa6a-0394e5d52a4b	3	20	f	\N	\N
46a30ae5-5ea7-4028-b1fc-b56dd5845e55	\N	identity-provider-redirector	apps	d552f890-1b2d-4a78-aa6a-0394e5d52a4b	2	25	f	\N	\N
f31d311f-a661-4bc5-86b1-afa668c39584	\N	\N	apps	d552f890-1b2d-4a78-aa6a-0394e5d52a4b	2	30	t	93ba0361-a9f6-4095-b0ab-66718fa8e029	\N
25e8bb71-047d-4e35-8173-d638eff676ef	\N	auth-username-password-form	apps	93ba0361-a9f6-4095-b0ab-66718fa8e029	0	10	f	\N	\N
9ad582a4-dffd-4277-8e7a-cd98ec5cb892	\N	\N	apps	93ba0361-a9f6-4095-b0ab-66718fa8e029	1	20	t	3a91c4a4-505a-4cf1-a3cc-0d9ea3c4bc93	\N
cfa5d920-6d1c-44a2-8633-14e535b2c86d	\N	conditional-user-configured	apps	3a91c4a4-505a-4cf1-a3cc-0d9ea3c4bc93	0	10	f	\N	\N
274c57f3-0876-45c5-9af3-58d60e4e7716	\N	auth-otp-form	apps	3a91c4a4-505a-4cf1-a3cc-0d9ea3c4bc93	0	20	f	\N	\N
327563db-8e60-4ae9-8d4c-5083e5b89a55	\N	direct-grant-validate-username	apps	932830d3-2f0b-4678-9250-d52008ec7dc3	0	10	f	\N	\N
f2fcffdc-6eaf-4144-a518-f85825576dc3	\N	direct-grant-validate-password	apps	932830d3-2f0b-4678-9250-d52008ec7dc3	0	20	f	\N	\N
a583b8fa-d822-4ebe-9e1a-a58d570ec58c	\N	\N	apps	932830d3-2f0b-4678-9250-d52008ec7dc3	1	30	t	0bcb3176-10a9-4f97-adc3-ad256709c452	\N
1a7facfe-e4ed-4a8b-94c2-12bb9ac37bab	\N	conditional-user-configured	apps	0bcb3176-10a9-4f97-adc3-ad256709c452	0	10	f	\N	\N
143fa71a-ee9a-45e5-af19-6d17daf283fb	\N	direct-grant-validate-otp	apps	0bcb3176-10a9-4f97-adc3-ad256709c452	0	20	f	\N	\N
b9ff0c25-b3c9-4093-9825-a10596ae9cbf	\N	registration-page-form	apps	3f738dab-c78b-474c-a2ce-ba9339898a0a	0	10	t	630fc8d4-9d6c-428b-9cd0-1ee102a9e55f	\N
d2025909-fa91-48e7-a90c-a526be0a4f0a	\N	registration-user-creation	apps	630fc8d4-9d6c-428b-9cd0-1ee102a9e55f	0	20	f	\N	\N
e96d126f-7cbd-48ac-8872-b5f26e15fbb0	\N	registration-profile-action	apps	630fc8d4-9d6c-428b-9cd0-1ee102a9e55f	0	40	f	\N	\N
fae027f3-9721-436f-acb5-082e485f38e5	\N	registration-password-action	apps	630fc8d4-9d6c-428b-9cd0-1ee102a9e55f	0	50	f	\N	\N
e3e7555a-47bf-4edd-8095-3847cd68f1ea	\N	registration-recaptcha-action	apps	630fc8d4-9d6c-428b-9cd0-1ee102a9e55f	3	60	f	\N	\N
aaad8774-e2db-463c-99fd-b6d0d1c22ff1	\N	reset-credentials-choose-user	apps	bb2d6bb2-2ae8-4d5a-81bf-4b7110190e4f	0	10	f	\N	\N
07b00570-d4ca-4d64-8e4b-02efaff32569	\N	reset-credential-email	apps	bb2d6bb2-2ae8-4d5a-81bf-4b7110190e4f	0	20	f	\N	\N
e3a020f0-da28-4a0d-814e-313c588ffeb7	\N	reset-password	apps	bb2d6bb2-2ae8-4d5a-81bf-4b7110190e4f	0	30	f	\N	\N
1401c3fb-8be8-4309-a7e7-471072de6839	\N	\N	apps	bb2d6bb2-2ae8-4d5a-81bf-4b7110190e4f	1	40	t	d4969807-7604-4b17-9bfe-67e9da605b13	\N
0fde3534-71f6-43fc-b6ed-0846cd7db0d3	\N	conditional-user-configured	apps	d4969807-7604-4b17-9bfe-67e9da605b13	0	10	f	\N	\N
4fc6193f-17e9-473f-940f-b17b3ac2912c	\N	reset-otp	apps	d4969807-7604-4b17-9bfe-67e9da605b13	0	20	f	\N	\N
0c4d702e-7bc5-4eef-87bf-f6b41d0c3cf3	\N	client-secret	apps	46cbff58-6904-4b46-8414-05add590377e	2	10	f	\N	\N
06773639-c281-4f46-abe7-659b08791d18	\N	client-jwt	apps	46cbff58-6904-4b46-8414-05add590377e	2	20	f	\N	\N
dd4e1687-d905-4207-961d-9b5aff105131	\N	client-secret-jwt	apps	46cbff58-6904-4b46-8414-05add590377e	2	30	f	\N	\N
89ba39d8-fee8-46bc-8795-bd73507a1551	\N	client-x509	apps	46cbff58-6904-4b46-8414-05add590377e	2	40	f	\N	\N
214fa9cf-ba7c-4125-8c50-ce2ca5b5f57a	\N	idp-review-profile	apps	e08ed2e9-02b3-4b7e-b1ea-5d9ffe5d358a	0	10	f	\N	428f2e05-75eb-4db3-ac7b-cdbde4fb5ac5
630e54d1-1e56-43cb-ac9d-9b855e0882f0	\N	\N	apps	e08ed2e9-02b3-4b7e-b1ea-5d9ffe5d358a	0	20	t	dd58700e-e960-4aef-8bd4-f47a474d7a4d	\N
a7347373-67f4-4830-9c5f-6e15fd69a4f4	\N	idp-create-user-if-unique	apps	dd58700e-e960-4aef-8bd4-f47a474d7a4d	2	10	f	\N	6a15775d-c81a-48b7-bc40-9ebe950e0140
a2651657-4d9b-4c32-ba53-94d8db166bcf	\N	\N	apps	dd58700e-e960-4aef-8bd4-f47a474d7a4d	2	20	t	9acd706c-70cb-4ed6-aff4-422663484f5f	\N
efa24257-fb17-4859-bf25-2289057ce97a	\N	idp-confirm-link	apps	9acd706c-70cb-4ed6-aff4-422663484f5f	0	10	f	\N	\N
b5084bca-6146-43dc-9c43-32ad6867433a	\N	\N	apps	9acd706c-70cb-4ed6-aff4-422663484f5f	0	20	t	01d308dc-0d5f-49bd-8400-3c52341fdd56	\N
2d2b5f64-11c5-4e8a-9c04-7ba6351c346d	\N	idp-email-verification	apps	01d308dc-0d5f-49bd-8400-3c52341fdd56	2	10	f	\N	\N
33c8678a-35a6-4735-81d0-4bc786fcf28a	\N	\N	apps	01d308dc-0d5f-49bd-8400-3c52341fdd56	2	20	t	b221da71-ad02-46c6-8a9b-766815bb0d47	\N
6a4c8065-a579-429f-8c81-39625c0e630b	\N	idp-username-password-form	apps	b221da71-ad02-46c6-8a9b-766815bb0d47	0	10	f	\N	\N
6b736179-69ba-4c6b-9b39-e188e47465ed	\N	\N	apps	b221da71-ad02-46c6-8a9b-766815bb0d47	1	20	t	a13174f1-ed72-4aa5-a79b-1bd3fa3a445b	\N
bff33023-e706-481f-a6b0-18785c3a50a3	\N	conditional-user-configured	apps	a13174f1-ed72-4aa5-a79b-1bd3fa3a445b	0	10	f	\N	\N
50695ea7-3b21-49e2-9864-5c16e31701b1	\N	auth-otp-form	apps	a13174f1-ed72-4aa5-a79b-1bd3fa3a445b	0	20	f	\N	\N
8d1b8bd4-09fb-4dc3-a220-c58f4c26a403	\N	http-basic-authenticator	apps	d1bc171e-43b9-4afb-a051-c4a3a42d80fe	0	10	f	\N	\N
5930d976-3efe-4695-8cb1-a5a190a61d39	\N	docker-http-basic-authenticator	apps	f370d353-46cb-4a3d-b074-e3fe18c223fd	0	10	f	\N	\N
ddc09aa0-1ce0-4df3-959f-7c939fc6110b	\N	no-cookie-redirect	apps	b6145048-47e7-4327-90ed-5f16df6d4847	0	10	f	\N	\N
9b986d86-ca6f-410a-9046-5140f9130d21	\N	\N	apps	b6145048-47e7-4327-90ed-5f16df6d4847	0	20	t	ed0f81a7-6839-4d72-8a2b-d0d253e3a928	\N
e5127f8d-99cc-458e-a7dc-91907d9e49de	\N	basic-auth	apps	ed0f81a7-6839-4d72-8a2b-d0d253e3a928	0	10	f	\N	\N
6b755d6b-30f8-4ead-b17e-76bc1afc615b	\N	basic-auth-otp	apps	ed0f81a7-6839-4d72-8a2b-d0d253e3a928	3	20	f	\N	\N
5d17cb94-998e-470f-9d18-b6190db1e597	\N	auth-spnego	apps	ed0f81a7-6839-4d72-8a2b-d0d253e3a928	3	30	f	\N	\N
\.


--
-- Data for Name: authentication_flow; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.authentication_flow (id, alias, description, realm_id, provider_id, top_level, built_in) FROM stdin;
671696be-a848-4d42-b76b-12256aeda5bf	browser	browser based authentication	master	basic-flow	t	t
f9fe24ad-c52a-4435-a505-1344558430db	forms	Username, password, otp and other auth forms.	master	basic-flow	f	t
5496fb50-3ae6-4867-802f-ea10ff9bb3c3	Browser - Conditional OTP	Flow to determine if the OTP is required for the authentication	master	basic-flow	f	t
6c5aa605-ea06-4926-816d-63d756e9fcc5	direct grant	OpenID Connect Resource Owner Grant	master	basic-flow	t	t
0930751d-69b3-497d-acc9-6b25e3cbe524	Direct Grant - Conditional OTP	Flow to determine if the OTP is required for the authentication	master	basic-flow	f	t
833f05e8-0902-4f4c-a2a7-154e3f7619d6	registration	registration flow	master	basic-flow	t	t
9cc1b3ac-ff29-4fd5-baf8-083222695e7a	registration form	registration form	master	form-flow	f	t
3374da34-b4fd-4870-91dc-110f78513d18	reset credentials	Reset credentials for a user if they forgot their password or something	master	basic-flow	t	t
0071d85e-1122-4941-b647-04bd94b80903	Reset - Conditional OTP	Flow to determine if the OTP should be reset or not. Set to REQUIRED to force.	master	basic-flow	f	t
2600c0ce-4c95-46aa-a62c-32cd8af0c837	clients	Base authentication for clients	master	client-flow	t	t
4d08f1c0-a049-4581-90db-b3545b1f2afa	first broker login	Actions taken after first broker login with identity provider account, which is not yet linked to any Keycloak account	master	basic-flow	t	t
8afa7bbb-0c3c-481c-995a-d4c9bb53d8dc	User creation or linking	Flow for the existing/non-existing user alternatives	master	basic-flow	f	t
75654d9d-278b-4e86-96ad-b0593f23d7a6	Handle Existing Account	Handle what to do if there is existing account with same email/username like authenticated identity provider	master	basic-flow	f	t
f3b0a0f8-6aba-40ac-8bf3-a83606a99ee5	Account verification options	Method with which to verity the existing account	master	basic-flow	f	t
b12fcbdc-c438-4af0-919d-f48a5d85b7a2	Verify Existing Account by Re-authentication	Reauthentication of existing account	master	basic-flow	f	t
7e9e5da4-1318-4aae-827b-61c7f2205a52	First broker login - Conditional OTP	Flow to determine if the OTP is required for the authentication	master	basic-flow	f	t
381652e9-b0d3-4595-bc7d-ce12f6c922f0	saml ecp	SAML ECP Profile Authentication Flow	master	basic-flow	t	t
43bbde40-8833-4e98-82ae-a1c85d4295bd	docker auth	Used by Docker clients to authenticate against the IDP	master	basic-flow	t	t
a0ae80a5-2c54-4988-ad28-8c5d1e26eb83	http challenge	An authentication flow based on challenge-response HTTP Authentication Schemes	master	basic-flow	t	t
2b7dece4-c69e-4873-bc2d-36e896914d24	Authentication Options	Authentication options.	master	basic-flow	f	t
d552f890-1b2d-4a78-aa6a-0394e5d52a4b	browser	browser based authentication	apps	basic-flow	t	t
93ba0361-a9f6-4095-b0ab-66718fa8e029	forms	Username, password, otp and other auth forms.	apps	basic-flow	f	t
3a91c4a4-505a-4cf1-a3cc-0d9ea3c4bc93	Browser - Conditional OTP	Flow to determine if the OTP is required for the authentication	apps	basic-flow	f	t
932830d3-2f0b-4678-9250-d52008ec7dc3	direct grant	OpenID Connect Resource Owner Grant	apps	basic-flow	t	t
0bcb3176-10a9-4f97-adc3-ad256709c452	Direct Grant - Conditional OTP	Flow to determine if the OTP is required for the authentication	apps	basic-flow	f	t
3f738dab-c78b-474c-a2ce-ba9339898a0a	registration	registration flow	apps	basic-flow	t	t
630fc8d4-9d6c-428b-9cd0-1ee102a9e55f	registration form	registration form	apps	form-flow	f	t
bb2d6bb2-2ae8-4d5a-81bf-4b7110190e4f	reset credentials	Reset credentials for a user if they forgot their password or something	apps	basic-flow	t	t
d4969807-7604-4b17-9bfe-67e9da605b13	Reset - Conditional OTP	Flow to determine if the OTP should be reset or not. Set to REQUIRED to force.	apps	basic-flow	f	t
46cbff58-6904-4b46-8414-05add590377e	clients	Base authentication for clients	apps	client-flow	t	t
e08ed2e9-02b3-4b7e-b1ea-5d9ffe5d358a	first broker login	Actions taken after first broker login with identity provider account, which is not yet linked to any Keycloak account	apps	basic-flow	t	t
dd58700e-e960-4aef-8bd4-f47a474d7a4d	User creation or linking	Flow for the existing/non-existing user alternatives	apps	basic-flow	f	t
9acd706c-70cb-4ed6-aff4-422663484f5f	Handle Existing Account	Handle what to do if there is existing account with same email/username like authenticated identity provider	apps	basic-flow	f	t
01d308dc-0d5f-49bd-8400-3c52341fdd56	Account verification options	Method with which to verity the existing account	apps	basic-flow	f	t
b221da71-ad02-46c6-8a9b-766815bb0d47	Verify Existing Account by Re-authentication	Reauthentication of existing account	apps	basic-flow	f	t
a13174f1-ed72-4aa5-a79b-1bd3fa3a445b	First broker login - Conditional OTP	Flow to determine if the OTP is required for the authentication	apps	basic-flow	f	t
d1bc171e-43b9-4afb-a051-c4a3a42d80fe	saml ecp	SAML ECP Profile Authentication Flow	apps	basic-flow	t	t
f370d353-46cb-4a3d-b074-e3fe18c223fd	docker auth	Used by Docker clients to authenticate against the IDP	apps	basic-flow	t	t
b6145048-47e7-4327-90ed-5f16df6d4847	http challenge	An authentication flow based on challenge-response HTTP Authentication Schemes	apps	basic-flow	t	t
ed0f81a7-6839-4d72-8a2b-d0d253e3a928	Authentication Options	Authentication options.	apps	basic-flow	f	t
\.


--
-- Data for Name: authenticator_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.authenticator_config (id, alias, realm_id) FROM stdin;
77387157-bee1-4fbf-ab5b-cc773b54c3a1	review profile config	master
d013cd7f-1246-4e13-a7bf-a8babfad367f	create unique user config	master
428f2e05-75eb-4db3-ac7b-cdbde4fb5ac5	review profile config	apps
6a15775d-c81a-48b7-bc40-9ebe950e0140	create unique user config	apps
\.


--
-- Data for Name: authenticator_config_entry; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.authenticator_config_entry (authenticator_id, value, name) FROM stdin;
77387157-bee1-4fbf-ab5b-cc773b54c3a1	missing	update.profile.on.first.login
d013cd7f-1246-4e13-a7bf-a8babfad367f	false	require.password.update.after.registration
428f2e05-75eb-4db3-ac7b-cdbde4fb5ac5	missing	update.profile.on.first.login
6a15775d-c81a-48b7-bc40-9ebe950e0140	false	require.password.update.after.registration
\.


--
-- Data for Name: broker_link; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.broker_link (identity_provider, storage_provider_id, realm_id, broker_user_id, broker_username, token, user_id) FROM stdin;
\.


--
-- Data for Name: client; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client (id, enabled, full_scope_allowed, client_id, not_before, public_client, secret, base_url, bearer_only, management_url, surrogate_auth_required, realm_id, protocol, node_rereg_timeout, frontchannel_logout, consent_required, name, service_accounts_enabled, client_authenticator_type, root_url, description, registration_token, standard_flow_enabled, implicit_flow_enabled, direct_access_grants_enabled, always_display_in_console) FROM stdin;
cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	t	master-realm	0	f	c9e9b8a6-3041-403b-b65e-4800ea5c66af	\N	t	\N	f	master	\N	0	f	f	master Realm	f	client-secret	\N	\N	\N	t	f	f	f
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	t	f	account	0	f	4d5d90ed-728e-441a-b05d-9de6de148eb8	/realms/master/account/	f	\N	f	master	openid-connect	0	f	f	${client_account}	f	client-secret	${authBaseUrl}	\N	\N	t	f	f	f
63083332-aa86-44e5-b715-e71acb73f51b	t	f	account-console	0	t	9510f259-39d5-4353-9b44-1342d64c6e07	/realms/master/account/	f	\N	f	master	openid-connect	0	f	f	${client_account-console}	f	client-secret	${authBaseUrl}	\N	\N	t	f	f	f
e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	t	f	broker	0	f	d53fbaec-129b-41f0-90c6-8701b41ea854	\N	f	\N	f	master	openid-connect	0	f	f	${client_broker}	f	client-secret	\N	\N	\N	t	f	f	f
2db59d5d-3b62-4da1-a063-c819ae967ff3	t	f	security-admin-console	0	t	ab42e9e0-96b9-480f-a2dd-b2e234724102	/admin/master/console/	f	\N	f	master	openid-connect	0	f	f	${client_security-admin-console}	f	client-secret	${authAdminUrl}	\N	\N	t	f	f	f
8fc3c695-beef-4faf-893b-3b4084ea6390	t	f	admin-cli	0	t	41ec91ed-2e5e-4ff6-9867-b1a68c8b46db	\N	f	\N	f	master	openid-connect	0	f	f	${client_admin-cli}	f	client-secret	\N	\N	\N	f	f	t	f
1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	t	apps-realm	0	f	b54d7988-57fa-4205-a7ab-5e3afbf381ce	\N	t	\N	f	master	\N	0	f	f	apps Realm	f	client-secret	\N	\N	\N	t	f	f	f
e915762a-6efc-4bd6-96bc-8bb512d4e371	t	f	realm-management	0	f	f5bbc3d8-db33-4f8b-b97f-68ea5a5c6a5a	\N	t	\N	f	apps	openid-connect	0	f	f	${client_realm-management}	f	client-secret	\N	\N	\N	t	f	f	f
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	t	f	account	0	f	6cf68974-fda1-42ed-903a-0dc536853182	/realms/apps/account/	f	\N	f	apps	openid-connect	0	f	f	${client_account}	f	client-secret	${authBaseUrl}	\N	\N	t	f	f	f
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	t	f	account-console	0	t	d7a24711-ceca-467a-8752-755dfad5a7a4	/realms/apps/account/	f	\N	f	apps	openid-connect	0	f	f	${client_account-console}	f	client-secret	${authBaseUrl}	\N	\N	t	f	f	f
9098959a-5e24-40f1-9b06-7bc629136be8	t	f	broker	0	f	e1aaf995-5156-420d-9c56-fdd5a93285d7	\N	f	\N	f	apps	openid-connect	0	f	f	${client_broker}	f	client-secret	\N	\N	\N	t	f	f	f
f17bfceb-76f1-4119-ba55-528255b3d1e7	t	f	security-admin-console	0	t	5c7db94e-71ad-471d-9747-06e2664fa545	/admin/apps/console/	f	\N	f	apps	openid-connect	0	f	f	${client_security-admin-console}	f	client-secret	${authAdminUrl}	\N	\N	t	f	f	f
7b330f03-9b9f-4dfe-9bf7-0e1527a9ee0b	t	f	admin-cli	0	t	d0a41afc-5b0b-492e-a3c6-1abf2e07fe4a	\N	f	\N	f	apps	openid-connect	0	f	f	${client_admin-cli}	f	client-secret	\N	\N	\N	f	f	t	f
cd7f999d-693c-4cb3-aec5-c96712243773	t	t	bbb-visio	0	f	e873443f-47cd-43a4-bae1-07ee1ade68c6	\N	f	http://localhost:5000	f	apps	openid-connect	-1	f	f	bbb-visio	f	client-secret	http://localhost:5000	bbb-visio	\N	t	f	t	f
\.


--
-- Data for Name: client_attributes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_attributes (client_id, value, name) FROM stdin;
63083332-aa86-44e5-b715-e71acb73f51b	S256	pkce.code.challenge.method
2db59d5d-3b62-4da1-a063-c819ae967ff3	S256	pkce.code.challenge.method
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	S256	pkce.code.challenge.method
f17bfceb-76f1-4119-ba55-528255b3d1e7	S256	pkce.code.challenge.method
cd7f999d-693c-4cb3-aec5-c96712243773	dsfr	login_theme
cd7f999d-693c-4cb3-aec5-c96712243773	false	saml.server.signature
cd7f999d-693c-4cb3-aec5-c96712243773	false	saml.server.signature.keyinfo.ext
cd7f999d-693c-4cb3-aec5-c96712243773	false	saml.assertion.signature
cd7f999d-693c-4cb3-aec5-c96712243773	false	saml.client.signature
cd7f999d-693c-4cb3-aec5-c96712243773	false	saml.encrypt
cd7f999d-693c-4cb3-aec5-c96712243773	false	saml.authnstatement
cd7f999d-693c-4cb3-aec5-c96712243773	false	saml.onetimeuse.condition
cd7f999d-693c-4cb3-aec5-c96712243773	false	saml_force_name_id_format
cd7f999d-693c-4cb3-aec5-c96712243773	false	saml.multivalued.roles
cd7f999d-693c-4cb3-aec5-c96712243773	false	saml.force.post.binding
cd7f999d-693c-4cb3-aec5-c96712243773	false	exclude.session.state.from.auth.response
cd7f999d-693c-4cb3-aec5-c96712243773	false	tls.client.certificate.bound.access.tokens
cd7f999d-693c-4cb3-aec5-c96712243773	false	display.on.consent.screen
\.


--
-- Data for Name: client_auth_flow_bindings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_auth_flow_bindings (client_id, flow_id, binding_name) FROM stdin;
\.


--
-- Data for Name: client_default_roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_default_roles (client_id, role_id) FROM stdin;
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	44f22444-e62d-495d-9d6e-33fc5df98fb5
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	03a27ca6-711a-444d-ba0b-f3a4713dbb94
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	8bf05a5c-d17d-4a60-9136-0b586d118c1a
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	fbd0725f-04a8-4c91-9275-6ee9881e9881
\.


--
-- Data for Name: client_initial_access; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_initial_access (id, realm_id, "timestamp", expiration, count, remaining_count) FROM stdin;
\.


--
-- Data for Name: client_node_registrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_node_registrations (client_id, value, name) FROM stdin;
\.


--
-- Data for Name: client_scope; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_scope (id, name, realm_id, description, protocol) FROM stdin;
1c70643e-3d79-45ee-8039-51c774b08f22	offline_access	master	OpenID Connect built-in scope: offline_access	openid-connect
1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1	role_list	master	SAML role list	saml
7261ff62-c1b7-434b-9512-93a9d2de5fec	profile	master	OpenID Connect built-in scope: profile	openid-connect
e2276247-2592-4fdf-adff-5e2eb7d6459f	email	master	OpenID Connect built-in scope: email	openid-connect
6e891f5e-cb60-448c-bb74-55796a2d7305	address	master	OpenID Connect built-in scope: address	openid-connect
4c5c75da-4e7b-43f7-ae66-6a16ca87c311	phone	master	OpenID Connect built-in scope: phone	openid-connect
1683580c-e145-4fa5-986b-1d5715078524	roles	master	OpenID Connect scope for add user roles to the access token	openid-connect
87ad8125-30a1-4b39-9cf1-c2da2948c00e	web-origins	master	OpenID Connect scope for add allowed web origins to the access token	openid-connect
f928b6a6-44d5-423e-b637-12f1c6640abd	microprofile-jwt	master	Microprofile - JWT built-in scope	openid-connect
bffb4877-c9b6-4650-aa25-470e7b40613f	offline_access	apps	OpenID Connect built-in scope: offline_access	openid-connect
22720f21-1408-47a3-a24b-b7a5c0ce35b6	role_list	apps	SAML role list	saml
e5f5b018-475a-4110-a625-ab398dfa05cc	profile	apps	OpenID Connect built-in scope: profile	openid-connect
087510cf-bea6-4e2b-bdc9-3ab3819a2e53	email	apps	OpenID Connect built-in scope: email	openid-connect
1ffcdc9a-3500-47e1-a93c-169a6db19f00	address	apps	OpenID Connect built-in scope: address	openid-connect
1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	phone	apps	OpenID Connect built-in scope: phone	openid-connect
0fddb81d-0a02-4519-9fd3-530e3639e88d	roles	apps	OpenID Connect scope for add user roles to the access token	openid-connect
e05868da-77ad-4f01-a50c-dff4c7bb4c51	web-origins	apps	OpenID Connect scope for add allowed web origins to the access token	openid-connect
ce6aa081-61c5-4d67-86b7-97cdbfb13667	microprofile-jwt	apps	Microprofile - JWT built-in scope	openid-connect
\.


--
-- Data for Name: client_scope_attributes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_scope_attributes (scope_id, value, name) FROM stdin;
1c70643e-3d79-45ee-8039-51c774b08f22	true	display.on.consent.screen
1c70643e-3d79-45ee-8039-51c774b08f22	${offlineAccessScopeConsentText}	consent.screen.text
1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1	true	display.on.consent.screen
1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1	${samlRoleListScopeConsentText}	consent.screen.text
7261ff62-c1b7-434b-9512-93a9d2de5fec	true	display.on.consent.screen
7261ff62-c1b7-434b-9512-93a9d2de5fec	${profileScopeConsentText}	consent.screen.text
7261ff62-c1b7-434b-9512-93a9d2de5fec	true	include.in.token.scope
e2276247-2592-4fdf-adff-5e2eb7d6459f	true	display.on.consent.screen
e2276247-2592-4fdf-adff-5e2eb7d6459f	${emailScopeConsentText}	consent.screen.text
e2276247-2592-4fdf-adff-5e2eb7d6459f	true	include.in.token.scope
6e891f5e-cb60-448c-bb74-55796a2d7305	true	display.on.consent.screen
6e891f5e-cb60-448c-bb74-55796a2d7305	${addressScopeConsentText}	consent.screen.text
6e891f5e-cb60-448c-bb74-55796a2d7305	true	include.in.token.scope
4c5c75da-4e7b-43f7-ae66-6a16ca87c311	true	display.on.consent.screen
4c5c75da-4e7b-43f7-ae66-6a16ca87c311	${phoneScopeConsentText}	consent.screen.text
4c5c75da-4e7b-43f7-ae66-6a16ca87c311	true	include.in.token.scope
1683580c-e145-4fa5-986b-1d5715078524	true	display.on.consent.screen
1683580c-e145-4fa5-986b-1d5715078524	${rolesScopeConsentText}	consent.screen.text
1683580c-e145-4fa5-986b-1d5715078524	false	include.in.token.scope
87ad8125-30a1-4b39-9cf1-c2da2948c00e	false	display.on.consent.screen
87ad8125-30a1-4b39-9cf1-c2da2948c00e		consent.screen.text
87ad8125-30a1-4b39-9cf1-c2da2948c00e	false	include.in.token.scope
f928b6a6-44d5-423e-b637-12f1c6640abd	false	display.on.consent.screen
f928b6a6-44d5-423e-b637-12f1c6640abd	true	include.in.token.scope
bffb4877-c9b6-4650-aa25-470e7b40613f	true	display.on.consent.screen
bffb4877-c9b6-4650-aa25-470e7b40613f	${offlineAccessScopeConsentText}	consent.screen.text
22720f21-1408-47a3-a24b-b7a5c0ce35b6	true	display.on.consent.screen
22720f21-1408-47a3-a24b-b7a5c0ce35b6	${samlRoleListScopeConsentText}	consent.screen.text
e5f5b018-475a-4110-a625-ab398dfa05cc	true	display.on.consent.screen
e5f5b018-475a-4110-a625-ab398dfa05cc	${profileScopeConsentText}	consent.screen.text
e5f5b018-475a-4110-a625-ab398dfa05cc	true	include.in.token.scope
087510cf-bea6-4e2b-bdc9-3ab3819a2e53	true	display.on.consent.screen
087510cf-bea6-4e2b-bdc9-3ab3819a2e53	${emailScopeConsentText}	consent.screen.text
087510cf-bea6-4e2b-bdc9-3ab3819a2e53	true	include.in.token.scope
1ffcdc9a-3500-47e1-a93c-169a6db19f00	true	display.on.consent.screen
1ffcdc9a-3500-47e1-a93c-169a6db19f00	${addressScopeConsentText}	consent.screen.text
1ffcdc9a-3500-47e1-a93c-169a6db19f00	true	include.in.token.scope
1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	true	display.on.consent.screen
1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	${phoneScopeConsentText}	consent.screen.text
1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	true	include.in.token.scope
0fddb81d-0a02-4519-9fd3-530e3639e88d	true	display.on.consent.screen
0fddb81d-0a02-4519-9fd3-530e3639e88d	${rolesScopeConsentText}	consent.screen.text
0fddb81d-0a02-4519-9fd3-530e3639e88d	false	include.in.token.scope
e05868da-77ad-4f01-a50c-dff4c7bb4c51	false	display.on.consent.screen
e05868da-77ad-4f01-a50c-dff4c7bb4c51		consent.screen.text
e05868da-77ad-4f01-a50c-dff4c7bb4c51	false	include.in.token.scope
ce6aa081-61c5-4d67-86b7-97cdbfb13667	false	display.on.consent.screen
ce6aa081-61c5-4d67-86b7-97cdbfb13667	true	include.in.token.scope
\.


--
-- Data for Name: client_scope_client; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_scope_client (client_id, scope_id, default_scope) FROM stdin;
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1	t
63083332-aa86-44e5-b715-e71acb73f51b	1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1	t
8fc3c695-beef-4faf-893b-3b4084ea6390	1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1	t
e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1	t
cbb309a2-43a4-45d3-bda7-84e6b87c6393	1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1	t
2db59d5d-3b62-4da1-a063-c819ae967ff3	1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1	t
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	7261ff62-c1b7-434b-9512-93a9d2de5fec	t
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	e2276247-2592-4fdf-adff-5e2eb7d6459f	t
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	1683580c-e145-4fa5-986b-1d5715078524	t
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	87ad8125-30a1-4b39-9cf1-c2da2948c00e	t
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	1c70643e-3d79-45ee-8039-51c774b08f22	f
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	6e891f5e-cb60-448c-bb74-55796a2d7305	f
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	4c5c75da-4e7b-43f7-ae66-6a16ca87c311	f
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	f928b6a6-44d5-423e-b637-12f1c6640abd	f
63083332-aa86-44e5-b715-e71acb73f51b	7261ff62-c1b7-434b-9512-93a9d2de5fec	t
63083332-aa86-44e5-b715-e71acb73f51b	e2276247-2592-4fdf-adff-5e2eb7d6459f	t
63083332-aa86-44e5-b715-e71acb73f51b	1683580c-e145-4fa5-986b-1d5715078524	t
63083332-aa86-44e5-b715-e71acb73f51b	87ad8125-30a1-4b39-9cf1-c2da2948c00e	t
63083332-aa86-44e5-b715-e71acb73f51b	1c70643e-3d79-45ee-8039-51c774b08f22	f
63083332-aa86-44e5-b715-e71acb73f51b	6e891f5e-cb60-448c-bb74-55796a2d7305	f
63083332-aa86-44e5-b715-e71acb73f51b	4c5c75da-4e7b-43f7-ae66-6a16ca87c311	f
63083332-aa86-44e5-b715-e71acb73f51b	f928b6a6-44d5-423e-b637-12f1c6640abd	f
8fc3c695-beef-4faf-893b-3b4084ea6390	7261ff62-c1b7-434b-9512-93a9d2de5fec	t
8fc3c695-beef-4faf-893b-3b4084ea6390	e2276247-2592-4fdf-adff-5e2eb7d6459f	t
8fc3c695-beef-4faf-893b-3b4084ea6390	1683580c-e145-4fa5-986b-1d5715078524	t
8fc3c695-beef-4faf-893b-3b4084ea6390	87ad8125-30a1-4b39-9cf1-c2da2948c00e	t
8fc3c695-beef-4faf-893b-3b4084ea6390	1c70643e-3d79-45ee-8039-51c774b08f22	f
8fc3c695-beef-4faf-893b-3b4084ea6390	6e891f5e-cb60-448c-bb74-55796a2d7305	f
8fc3c695-beef-4faf-893b-3b4084ea6390	4c5c75da-4e7b-43f7-ae66-6a16ca87c311	f
8fc3c695-beef-4faf-893b-3b4084ea6390	f928b6a6-44d5-423e-b637-12f1c6640abd	f
e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	7261ff62-c1b7-434b-9512-93a9d2de5fec	t
e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	e2276247-2592-4fdf-adff-5e2eb7d6459f	t
e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	1683580c-e145-4fa5-986b-1d5715078524	t
e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	87ad8125-30a1-4b39-9cf1-c2da2948c00e	t
e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	1c70643e-3d79-45ee-8039-51c774b08f22	f
e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	6e891f5e-cb60-448c-bb74-55796a2d7305	f
e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	4c5c75da-4e7b-43f7-ae66-6a16ca87c311	f
e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	f928b6a6-44d5-423e-b637-12f1c6640abd	f
cbb309a2-43a4-45d3-bda7-84e6b87c6393	7261ff62-c1b7-434b-9512-93a9d2de5fec	t
cbb309a2-43a4-45d3-bda7-84e6b87c6393	e2276247-2592-4fdf-adff-5e2eb7d6459f	t
cbb309a2-43a4-45d3-bda7-84e6b87c6393	1683580c-e145-4fa5-986b-1d5715078524	t
cbb309a2-43a4-45d3-bda7-84e6b87c6393	87ad8125-30a1-4b39-9cf1-c2da2948c00e	t
cbb309a2-43a4-45d3-bda7-84e6b87c6393	1c70643e-3d79-45ee-8039-51c774b08f22	f
cbb309a2-43a4-45d3-bda7-84e6b87c6393	6e891f5e-cb60-448c-bb74-55796a2d7305	f
cbb309a2-43a4-45d3-bda7-84e6b87c6393	4c5c75da-4e7b-43f7-ae66-6a16ca87c311	f
cbb309a2-43a4-45d3-bda7-84e6b87c6393	f928b6a6-44d5-423e-b637-12f1c6640abd	f
2db59d5d-3b62-4da1-a063-c819ae967ff3	7261ff62-c1b7-434b-9512-93a9d2de5fec	t
2db59d5d-3b62-4da1-a063-c819ae967ff3	e2276247-2592-4fdf-adff-5e2eb7d6459f	t
2db59d5d-3b62-4da1-a063-c819ae967ff3	1683580c-e145-4fa5-986b-1d5715078524	t
2db59d5d-3b62-4da1-a063-c819ae967ff3	87ad8125-30a1-4b39-9cf1-c2da2948c00e	t
2db59d5d-3b62-4da1-a063-c819ae967ff3	1c70643e-3d79-45ee-8039-51c774b08f22	f
2db59d5d-3b62-4da1-a063-c819ae967ff3	6e891f5e-cb60-448c-bb74-55796a2d7305	f
2db59d5d-3b62-4da1-a063-c819ae967ff3	4c5c75da-4e7b-43f7-ae66-6a16ca87c311	f
2db59d5d-3b62-4da1-a063-c819ae967ff3	f928b6a6-44d5-423e-b637-12f1c6640abd	f
1229b670-54d4-4b05-8abd-7b4a230e8bf6	1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1	t
1229b670-54d4-4b05-8abd-7b4a230e8bf6	7261ff62-c1b7-434b-9512-93a9d2de5fec	t
1229b670-54d4-4b05-8abd-7b4a230e8bf6	e2276247-2592-4fdf-adff-5e2eb7d6459f	t
1229b670-54d4-4b05-8abd-7b4a230e8bf6	1683580c-e145-4fa5-986b-1d5715078524	t
1229b670-54d4-4b05-8abd-7b4a230e8bf6	87ad8125-30a1-4b39-9cf1-c2da2948c00e	t
1229b670-54d4-4b05-8abd-7b4a230e8bf6	1c70643e-3d79-45ee-8039-51c774b08f22	f
1229b670-54d4-4b05-8abd-7b4a230e8bf6	6e891f5e-cb60-448c-bb74-55796a2d7305	f
1229b670-54d4-4b05-8abd-7b4a230e8bf6	4c5c75da-4e7b-43f7-ae66-6a16ca87c311	f
1229b670-54d4-4b05-8abd-7b4a230e8bf6	f928b6a6-44d5-423e-b637-12f1c6640abd	f
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	22720f21-1408-47a3-a24b-b7a5c0ce35b6	t
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	22720f21-1408-47a3-a24b-b7a5c0ce35b6	t
7b330f03-9b9f-4dfe-9bf7-0e1527a9ee0b	22720f21-1408-47a3-a24b-b7a5c0ce35b6	t
9098959a-5e24-40f1-9b06-7bc629136be8	22720f21-1408-47a3-a24b-b7a5c0ce35b6	t
e915762a-6efc-4bd6-96bc-8bb512d4e371	22720f21-1408-47a3-a24b-b7a5c0ce35b6	t
f17bfceb-76f1-4119-ba55-528255b3d1e7	22720f21-1408-47a3-a24b-b7a5c0ce35b6	t
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	e5f5b018-475a-4110-a625-ab398dfa05cc	t
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	087510cf-bea6-4e2b-bdc9-3ab3819a2e53	t
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	0fddb81d-0a02-4519-9fd3-530e3639e88d	t
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	e05868da-77ad-4f01-a50c-dff4c7bb4c51	t
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	bffb4877-c9b6-4650-aa25-470e7b40613f	f
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	1ffcdc9a-3500-47e1-a93c-169a6db19f00	f
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	f
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	ce6aa081-61c5-4d67-86b7-97cdbfb13667	f
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	e5f5b018-475a-4110-a625-ab398dfa05cc	t
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	087510cf-bea6-4e2b-bdc9-3ab3819a2e53	t
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	0fddb81d-0a02-4519-9fd3-530e3639e88d	t
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	e05868da-77ad-4f01-a50c-dff4c7bb4c51	t
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	bffb4877-c9b6-4650-aa25-470e7b40613f	f
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	1ffcdc9a-3500-47e1-a93c-169a6db19f00	f
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	f
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	ce6aa081-61c5-4d67-86b7-97cdbfb13667	f
7b330f03-9b9f-4dfe-9bf7-0e1527a9ee0b	e5f5b018-475a-4110-a625-ab398dfa05cc	t
7b330f03-9b9f-4dfe-9bf7-0e1527a9ee0b	087510cf-bea6-4e2b-bdc9-3ab3819a2e53	t
7b330f03-9b9f-4dfe-9bf7-0e1527a9ee0b	0fddb81d-0a02-4519-9fd3-530e3639e88d	t
7b330f03-9b9f-4dfe-9bf7-0e1527a9ee0b	e05868da-77ad-4f01-a50c-dff4c7bb4c51	t
7b330f03-9b9f-4dfe-9bf7-0e1527a9ee0b	bffb4877-c9b6-4650-aa25-470e7b40613f	f
7b330f03-9b9f-4dfe-9bf7-0e1527a9ee0b	1ffcdc9a-3500-47e1-a93c-169a6db19f00	f
7b330f03-9b9f-4dfe-9bf7-0e1527a9ee0b	1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	f
7b330f03-9b9f-4dfe-9bf7-0e1527a9ee0b	ce6aa081-61c5-4d67-86b7-97cdbfb13667	f
9098959a-5e24-40f1-9b06-7bc629136be8	e5f5b018-475a-4110-a625-ab398dfa05cc	t
9098959a-5e24-40f1-9b06-7bc629136be8	087510cf-bea6-4e2b-bdc9-3ab3819a2e53	t
9098959a-5e24-40f1-9b06-7bc629136be8	0fddb81d-0a02-4519-9fd3-530e3639e88d	t
9098959a-5e24-40f1-9b06-7bc629136be8	e05868da-77ad-4f01-a50c-dff4c7bb4c51	t
9098959a-5e24-40f1-9b06-7bc629136be8	bffb4877-c9b6-4650-aa25-470e7b40613f	f
9098959a-5e24-40f1-9b06-7bc629136be8	1ffcdc9a-3500-47e1-a93c-169a6db19f00	f
9098959a-5e24-40f1-9b06-7bc629136be8	1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	f
9098959a-5e24-40f1-9b06-7bc629136be8	ce6aa081-61c5-4d67-86b7-97cdbfb13667	f
e915762a-6efc-4bd6-96bc-8bb512d4e371	e5f5b018-475a-4110-a625-ab398dfa05cc	t
e915762a-6efc-4bd6-96bc-8bb512d4e371	087510cf-bea6-4e2b-bdc9-3ab3819a2e53	t
e915762a-6efc-4bd6-96bc-8bb512d4e371	0fddb81d-0a02-4519-9fd3-530e3639e88d	t
e915762a-6efc-4bd6-96bc-8bb512d4e371	e05868da-77ad-4f01-a50c-dff4c7bb4c51	t
e915762a-6efc-4bd6-96bc-8bb512d4e371	bffb4877-c9b6-4650-aa25-470e7b40613f	f
e915762a-6efc-4bd6-96bc-8bb512d4e371	1ffcdc9a-3500-47e1-a93c-169a6db19f00	f
e915762a-6efc-4bd6-96bc-8bb512d4e371	1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	f
e915762a-6efc-4bd6-96bc-8bb512d4e371	ce6aa081-61c5-4d67-86b7-97cdbfb13667	f
f17bfceb-76f1-4119-ba55-528255b3d1e7	e5f5b018-475a-4110-a625-ab398dfa05cc	t
f17bfceb-76f1-4119-ba55-528255b3d1e7	087510cf-bea6-4e2b-bdc9-3ab3819a2e53	t
f17bfceb-76f1-4119-ba55-528255b3d1e7	0fddb81d-0a02-4519-9fd3-530e3639e88d	t
f17bfceb-76f1-4119-ba55-528255b3d1e7	e05868da-77ad-4f01-a50c-dff4c7bb4c51	t
f17bfceb-76f1-4119-ba55-528255b3d1e7	bffb4877-c9b6-4650-aa25-470e7b40613f	f
f17bfceb-76f1-4119-ba55-528255b3d1e7	1ffcdc9a-3500-47e1-a93c-169a6db19f00	f
f17bfceb-76f1-4119-ba55-528255b3d1e7	1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	f
f17bfceb-76f1-4119-ba55-528255b3d1e7	ce6aa081-61c5-4d67-86b7-97cdbfb13667	f
cd7f999d-693c-4cb3-aec5-c96712243773	22720f21-1408-47a3-a24b-b7a5c0ce35b6	t
cd7f999d-693c-4cb3-aec5-c96712243773	e5f5b018-475a-4110-a625-ab398dfa05cc	t
cd7f999d-693c-4cb3-aec5-c96712243773	087510cf-bea6-4e2b-bdc9-3ab3819a2e53	t
cd7f999d-693c-4cb3-aec5-c96712243773	0fddb81d-0a02-4519-9fd3-530e3639e88d	t
cd7f999d-693c-4cb3-aec5-c96712243773	e05868da-77ad-4f01-a50c-dff4c7bb4c51	t
cd7f999d-693c-4cb3-aec5-c96712243773	bffb4877-c9b6-4650-aa25-470e7b40613f	f
cd7f999d-693c-4cb3-aec5-c96712243773	1ffcdc9a-3500-47e1-a93c-169a6db19f00	f
cd7f999d-693c-4cb3-aec5-c96712243773	1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	f
cd7f999d-693c-4cb3-aec5-c96712243773	ce6aa081-61c5-4d67-86b7-97cdbfb13667	f
\.


--
-- Data for Name: client_scope_role_mapping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_scope_role_mapping (scope_id, role_id) FROM stdin;
1c70643e-3d79-45ee-8039-51c774b08f22	8055ea0c-2ec5-49a9-84aa-57f6f07da327
bffb4877-c9b6-4650-aa25-470e7b40613f	37849908-4303-45b1-ab4f-90e2e8b23ffa
\.


--
-- Data for Name: client_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_session (id, client_id, redirect_uri, state, "timestamp", session_id, auth_method, realm_id, auth_user_id, current_action) FROM stdin;
\.


--
-- Data for Name: client_session_auth_status; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_session_auth_status (authenticator, status, client_session) FROM stdin;
\.


--
-- Data for Name: client_session_note; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_session_note (name, value, client_session) FROM stdin;
\.


--
-- Data for Name: client_session_prot_mapper; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_session_prot_mapper (protocol_mapper_id, client_session) FROM stdin;
\.


--
-- Data for Name: client_session_role; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_session_role (role_id, client_session) FROM stdin;
\.


--
-- Data for Name: client_user_session_note; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_user_session_note (name, value, client_session) FROM stdin;
\.


--
-- Data for Name: component; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.component (id, name, parent_id, provider_id, provider_type, realm_id, sub_type) FROM stdin;
3239bce2-7b03-4fdd-98a3-8c7c8f3cea63	Trusted Hosts	master	trusted-hosts	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	master	anonymous
71eeb170-8749-4da6-92f4-232409df9cab	Consent Required	master	consent-required	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	master	anonymous
74ee321f-b825-4dca-9ef4-99285c49e697	Full Scope Disabled	master	scope	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	master	anonymous
ebc27ad8-ba2f-4c4e-b5b6-8dfd004b9f94	Max Clients Limit	master	max-clients	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	master	anonymous
050ef0bc-0be1-4dbc-b698-8a406386bea3	Allowed Protocol Mapper Types	master	allowed-protocol-mappers	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	master	anonymous
10080c8e-8a17-4693-acbb-42284765d948	Allowed Client Scopes	master	allowed-client-templates	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	master	anonymous
c0e35243-d263-4fd4-a7e8-61bd37a5737d	Allowed Protocol Mapper Types	master	allowed-protocol-mappers	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	master	authenticated
244a4761-9e39-4e68-9cca-2ab16dafd362	Allowed Client Scopes	master	allowed-client-templates	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	master	authenticated
b9b8ea3e-87eb-47e0-90d9-d535f434751c	rsa-generated	master	rsa-generated	org.keycloak.keys.KeyProvider	master	\N
52eece9e-e9ae-4453-b966-013d76fbde61	hmac-generated	master	hmac-generated	org.keycloak.keys.KeyProvider	master	\N
424a2b30-2962-4565-b487-84363ae0b54b	aes-generated	master	aes-generated	org.keycloak.keys.KeyProvider	master	\N
b6b7ab04-c2b3-4c45-b84f-a9c4f97bb479	rsa-generated	apps	rsa-generated	org.keycloak.keys.KeyProvider	apps	\N
633e5af8-5ce0-410e-8eb0-473974154209	hmac-generated	apps	hmac-generated	org.keycloak.keys.KeyProvider	apps	\N
af204def-d5e6-4e68-884d-a5d16f8cf705	aes-generated	apps	aes-generated	org.keycloak.keys.KeyProvider	apps	\N
43466fdd-c8dc-439e-adff-752e77c60907	Trusted Hosts	apps	trusted-hosts	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	apps	anonymous
7f064b59-8e2b-4fb0-89ba-38f7246f972b	Consent Required	apps	consent-required	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	apps	anonymous
8aeac511-8f6a-4502-a472-3cfe2414a7bd	Full Scope Disabled	apps	scope	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	apps	anonymous
1096522e-9c38-4165-8d01-aa0763e15926	Max Clients Limit	apps	max-clients	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	apps	anonymous
4f93b1da-074f-4c15-93b6-15367fdfb745	Allowed Protocol Mapper Types	apps	allowed-protocol-mappers	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	apps	anonymous
9b1c0c05-d6e0-40be-a349-448508cf213a	Allowed Client Scopes	apps	allowed-client-templates	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	apps	anonymous
93cd1db3-9084-4768-910b-4b41dbd3aebe	Allowed Protocol Mapper Types	apps	allowed-protocol-mappers	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	apps	authenticated
8943e57f-51ec-4e12-9b7b-070d822327c4	Allowed Client Scopes	apps	allowed-client-templates	org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy	apps	authenticated
\.


--
-- Data for Name: component_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.component_config (id, component_id, name, value) FROM stdin;
7e651f7d-2988-4309-959d-b9b3b99a74dd	ebc27ad8-ba2f-4c4e-b5b6-8dfd004b9f94	max-clients	200
eaefa53a-78f8-4088-860d-88a6de7fc7e1	10080c8e-8a17-4693-acbb-42284765d948	allow-default-scopes	true
d5c706c4-062b-4d52-b9c1-13d105982639	3239bce2-7b03-4fdd-98a3-8c7c8f3cea63	host-sending-registration-request-must-match	true
8b4a3ec6-61e2-4330-b2ad-7545158d57f5	3239bce2-7b03-4fdd-98a3-8c7c8f3cea63	client-uris-must-match	true
48d7ec64-b481-4842-b1cb-77628f6bb29c	050ef0bc-0be1-4dbc-b698-8a406386bea3	allowed-protocol-mapper-types	oidc-usermodel-property-mapper
87237385-a43f-49d3-aa54-67a986c5b2ff	050ef0bc-0be1-4dbc-b698-8a406386bea3	allowed-protocol-mapper-types	oidc-address-mapper
9e31bb37-5479-4949-8365-0a84e401cfe6	050ef0bc-0be1-4dbc-b698-8a406386bea3	allowed-protocol-mapper-types	oidc-usermodel-attribute-mapper
2a9abd48-5f01-43f9-845e-293458ab3aa3	050ef0bc-0be1-4dbc-b698-8a406386bea3	allowed-protocol-mapper-types	saml-user-property-mapper
b3346be9-fd83-48e3-aa52-4e38a1496866	050ef0bc-0be1-4dbc-b698-8a406386bea3	allowed-protocol-mapper-types	saml-role-list-mapper
6d14758b-d8f2-4457-9918-91cc5120781e	050ef0bc-0be1-4dbc-b698-8a406386bea3	allowed-protocol-mapper-types	saml-user-attribute-mapper
aee019a9-790a-45fc-bcb6-cb39aacb79d5	050ef0bc-0be1-4dbc-b698-8a406386bea3	allowed-protocol-mapper-types	oidc-sha256-pairwise-sub-mapper
49db3402-f0f6-4976-9df8-15e4c18a04fd	050ef0bc-0be1-4dbc-b698-8a406386bea3	allowed-protocol-mapper-types	oidc-full-name-mapper
bfede4e4-3afd-4f37-b2df-d60386403c8d	c0e35243-d263-4fd4-a7e8-61bd37a5737d	allowed-protocol-mapper-types	oidc-full-name-mapper
19850c5a-6dc5-4e7e-83a8-4a7defe6784a	c0e35243-d263-4fd4-a7e8-61bd37a5737d	allowed-protocol-mapper-types	saml-user-attribute-mapper
14f96ce8-c2e2-45f9-a692-81215d335397	c0e35243-d263-4fd4-a7e8-61bd37a5737d	allowed-protocol-mapper-types	oidc-usermodel-property-mapper
5bc82512-1667-48d9-948d-796f8c2faf33	c0e35243-d263-4fd4-a7e8-61bd37a5737d	allowed-protocol-mapper-types	oidc-address-mapper
6cd54d6a-6e2c-4576-81da-9c715317b5c1	c0e35243-d263-4fd4-a7e8-61bd37a5737d	allowed-protocol-mapper-types	oidc-usermodel-attribute-mapper
72f47588-beee-4d40-b543-00b3b55e61c5	c0e35243-d263-4fd4-a7e8-61bd37a5737d	allowed-protocol-mapper-types	saml-role-list-mapper
c228828d-edbc-4dfe-a9c1-ca1259e4ad45	c0e35243-d263-4fd4-a7e8-61bd37a5737d	allowed-protocol-mapper-types	oidc-sha256-pairwise-sub-mapper
1efdd314-be91-474a-85c2-aa22abb978aa	c0e35243-d263-4fd4-a7e8-61bd37a5737d	allowed-protocol-mapper-types	saml-user-property-mapper
0d4e2008-beac-4367-8772-7bc3ed64f4f1	244a4761-9e39-4e68-9cca-2ab16dafd362	allow-default-scopes	true
d5ec7920-dec4-40e7-bc25-f688c0c8970b	424a2b30-2962-4565-b487-84363ae0b54b	kid	8a37a518-3a0f-46b6-ba20-436b17159851
222afc88-2fe4-4eb1-9964-bdaf5db9c6dc	424a2b30-2962-4565-b487-84363ae0b54b	priority	100
6103fbbb-ed6b-489b-89fc-f8850d87790d	424a2b30-2962-4565-b487-84363ae0b54b	secret	q2zJaaDuf8pg0MhazjBStw
4ab01cae-aa06-400b-aa9c-6f3fea4f1b9b	b9b8ea3e-87eb-47e0-90d9-d535f434751c	certificate	MIICmzCCAYMCBgF14lN2sTANBgkqhkiG9w0BAQsFADARMQ8wDQYDVQQDDAZtYXN0ZXIwHhcNMjAxMTE5MjEwMzQyWhcNMzAxMTE5MjEwNTIyWjARMQ8wDQYDVQQDDAZtYXN0ZXIwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCWSDfveTN3EftRWT4lmSyxXUzrMIGF+eyjI/Pznk6rGz8CGKlKygSiQEMI6waNkVQjxwi044+2xnRRsXKpqZpAkdhOYB5Do3jpli+OciYNWyrtE5TUa/EOEwK9qoMPa7NnR3ZfiVtqv3UoLVMVj1pfjjR4VKee3nGQbHAyyhT4dXVKD+2pnGyqpORDS7uE42dnQw2YAGYLrRdz27LQRinHkBmYzhGl+tunqKAanDAli/fSk7MUy0/wnZyecd/qd2X+2EYMmN/R8COWZZtrKmcLYqh3sGhw9DVfPn1JZNoFaGlKzxnLlUlbWjK4nBSnKY59eWcGcbG88X4Ji0l+SgyJAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAIETBTLjKMriLkUqn8hJnGAHBgyn3opOYhp5zDLUMlRZZq5IAOQWEZVp6QuJqsMbNcWoCh4nZTYQOteY3x5fKkQMWhspjzr+1kgdgjl3Lg7vNJ8vxOOBCUGUq5nR7wYGLkISKXyAIpICcMhrN2ky1mFFAn0nkWdv3iKHmpXzPPKViHHAW62z6n7QkMD8fM1koXh5SHQ4grzEq4WeYN0nU5Y+iQg59o8njtg/F2MGvZ5EDprGvU6Ki3pkMi2v9LlnpU0AGei53YqFVpo5XY4UcRZnh9LCscNh22MQqxgMKxQtMi7SCx2IEgxmZ8ZTo4zp3buGCgA+Lx67dqOu45DAQcU=
dff95448-0ec3-4db9-8b64-10b0b798f690	b9b8ea3e-87eb-47e0-90d9-d535f434751c	priority	100
6dc42a68-f18b-4aab-a906-769365ff34a7	b9b8ea3e-87eb-47e0-90d9-d535f434751c	privateKey	MIIEpQIBAAKCAQEAlkg373kzdxH7UVk+JZkssV1M6zCBhfnsoyPz855Oqxs/AhipSsoEokBDCOsGjZFUI8cItOOPtsZ0UbFyqamaQJHYTmAeQ6N46ZYvjnImDVsq7ROU1GvxDhMCvaqDD2uzZ0d2X4lbar91KC1TFY9aX440eFSnnt5xkGxwMsoU+HV1Sg/tqZxsqqTkQ0u7hONnZ0MNmABmC60Xc9uy0EYpx5AZmM4Rpfrbp6igGpwwJYv30pOzFMtP8J2cnnHf6ndl/thGDJjf0fAjlmWbaypnC2Kod7BocPQ1Xz59SWTaBWhpSs8Zy5VJW1oyuJwUpymOfXlnBnGxvPF+CYtJfkoMiQIDAQABAoIBABM0YWmJ7Ii/1IT9yZJWc76qtKStiy/K03G5q3grd9Qn5DJpYmD7VgJCAg8GscyvkLgNvFAZcIkj7UNvUL7bvKmZubGyWMu9/TqkhalHbxNv3hlz0iYfMSviRAxm2N7EnaWKHVdyHyuSEe+zcxWjPyJM8umZr93+gTa6lM/4wRtK/NYDmQJOX6mTFuSzNkWvlIsiWIwpP4SXGVeEX7M8Jc+i5KhyP/DOS4utMo4HPohmbxyoQDGvUQmo2w5wWw6nIGF2FvwEz2bVQBIyBP4XHpJO14/hUB5lcEw0ykp0iaBoHs776t3CC9Jtj628Nj4VCI66XryvsX/AHjJn4xB7sJ0CgYEA3UrOYqpccOZQg5gefU5gxInfMDvBNXolnwNMh31/nRMEmz0P2Hs1minKDl7nuJYgsCSWxzmdrQjKpHEd26kCWCxI3coSIkvrPiooeVtaM5uBJPcicO0ws8L0jWZvtbMuFB6N1duF0jtnN4VgPX8mzQ7MZruWvE+X4xfhDm879VsCgYEArdpBqh4MyNAi2DFVMfVoIKB5Hlx3kLzaxJ/ycdqPQJGtQuUVirfz+3aSW7bSAiHOZMbbyoJlRu4Afh0F9qct3K7fuWG93uIZGqBqB80cwF6BkTw9ounm8WfNZCgTP39C0uR2B2TkCs+TjBworO8d6QYrOrRcKRJ0ebOUmveeFusCgYEAg/GqhSHW5Gou74ewBj7Ja+ZY8UVvuhcOf3VUGCU4BcvlHzqVTBqKp1TraQ4lU+YPr3bhgABWh2mKien4R5TKFRCykat+jHx/0x0H7PQPIF5D7mp8WqDSPRys+/JsAQbJHq3pG+48KFHLBUu9Sm2aEQIV1dtb0QQUKA+A3T5tnakCgYEAoYPBuaBNVEs59AxxEAbkhFtR6wkQ8+DghgfrICdjKyOsChf2WXfpLdfMxXQly2FI9ItjKtLV8H2w63lfTvWmP/4fT4Uk9uqrU/dwSmseqQGj8iA7Sx1vNxuuz7wDldxPYsppdRkgW4LZmzOV/oPwD8txYgqqDGZe26ohB4/AyZ0CgYEAno40K0sKZP1CpyQdX9hNKXbXi4u7wiok5KvM6zX3pu6ILnvuqyUHEEmxMnBz8d0kkndXEsSitBl7GlfOmm+iI6KNFygQ98jblXBQ2ZJpk/jpm1Jh2HeztQOXOOGjjxsU0Cpj9xBnk3X0FLLXOD1S7ieCzlV70OmPcp+eZlVlHOM=
859550a7-dccc-4ca9-b3dd-3a5846e422da	52eece9e-e9ae-4453-b966-013d76fbde61	secret	vFHKXmoyjSkaXnGq6eREGuyJqGtWjhbQ77Pv6tdo8i4HPQe9k4uioI4J0vpq18RM9OEwt8EPyaBmTcqx2rFnjw
dd4d67ce-6b91-4303-b373-718a7fb6fbdc	52eece9e-e9ae-4453-b966-013d76fbde61	algorithm	HS256
bbdb32a2-a9b6-4005-8687-afe8652db5b7	52eece9e-e9ae-4453-b966-013d76fbde61	kid	1e4b29b9-b822-4c36-9888-1b91007059c4
25feabb7-34a8-4fb8-9c20-1cf5290160cc	52eece9e-e9ae-4453-b966-013d76fbde61	priority	100
0a2e554f-19ab-42d2-b76d-f1bbc9ecc245	b6b7ab04-c2b3-4c45-b84f-a9c4f97bb479	priority	100
d664f997-a7ac-4ec9-89a2-9e833ef3127f	b6b7ab04-c2b3-4c45-b84f-a9c4f97bb479	privateKey	MIIEowIBAAKCAQEAgIRcnYEBkugpqDLfw8I1EHIl9i5RhNn5pB8NmJ5NdJ2/XobEqY2VvSxAcj4NIhRt2QXS5Y4bqtrTDyTgc+9m/1oq4dxz7k8cXMrGhkJVPUjsHqLcBXcyB0fEgAYQuV1DRRL8SHyFkTRvIdrQzGU557xefiXV+AXXrnuG6/84Q70zE5fGwYnmYPJWqlDLxqhocVsB0KjCLb9MH4/oZ9EiZP7dPdW1Mgt3CC1IB1u3Im+cs1wVddUB22Xowk7bdgC7kumvrEy9t4shsAuFKVDJVcnhkBMHQa7iM6xxa3ACIuYDt5NXZODnSoJSK3YMWVfe7T46dSC7DB+k6T1NwTI06wIDAQABAoIBAFQCMehjY/v79v8UAmGcmcNeWqJKNM97DUzTX7fcAxWv6GCKCBQtkSxPuPD0zvDwGb47qFiWRE+zKzRDDtW6MMHK1y09RisJW6jshElPIxkkifSc0OZhvDo2F6T4UgZZiJemiXN4snbwp5ShzMtPgEKTR9F+Ohge+ZX8+X1bIBRmscbrjkaUIKb6vYYHZ+JmzhBLeuPz2kR9cKaxlPmeJYzqHSMoYQGdH8tQQDIfK7iK5hF3OoowIoiyYrhRZkqU9ZOpxLdAJWlKZy1HTAHbB7fwYPCFzZqj3SdmTYJyrXwIF6FmyMLiTs017pPBc7MSlSful1xwlOpNgiIl65aqCkECgYEAzsv4EvInFY8WfWW2ZqxwbUkbebSDQr7aPB2KXeLcfmafRYVDAuX+OgJjNLcyQSu0O76uAVqg06UCF/cHvqd0nctp/u0q5bHF7cQaxU1mR2a6w2qnOBAsTGFEm3H7JXM+FAuvw0IC6RKZ8rUyBCUSj2Xj4lJoZh0wAVKNGz0Nc/8CgYEAnxhcHytNWwH6m9U75TYMqo/hw/dX8YsmVaLf8Z4I9ok0E77ZtgOW3OHvS5D9ikhwtuJvMKNKekQ5ZDYA5OXnqdi2eTztkHLdPw/ygrVj7MMTv+pjdFwYphqq1Iko2evPZuPhCDLdH1nGEtG30igXLTyoalTeYIhtDg3eJve0TxUCgYEAvieyooFGzT04+e/YbMstymBKQnxpoqtqc5LaVACyrgxhcoTanMSuI9tkK+o07NZqMfHhgV87ucHmjfDaj0beJecRPZgKNRJmJX+I+lp0rT1aiSz+PMAqa8WZV7LUtJgmwjoI0exWTsmLBDH3nvYT/gY8KTWLyDIYnW6yUBSw1TMCgYBIPKpPaLz17p8YtKg+ed0kcLIk5aDjxrfAOHUQYx5UupWPxZ9auqR8ZIXfvNSyPhQXphawceQ2QdYBP1gGlrEqeIDZ6aVAajc1FAub97qIXUcRY96Gje6PNRqN6D1JPX3tjNi3fUjTnFKIZvrdDGEBpEIgDarvD+Lcd8V/0gbnxQKBgG1J2u7dnKdXsdZYJTple8ki5Ke3pY4Xk2EDztGil6psss++wuLTnNPNn/IJvVYREt5KhuZIvDMLie8VXLnehEvvW3J9K8j7KzEhEX/S1uR81z+MQQ2zMBxtYzqjp0/lNRJSvgzUd4PB7PZ7lU2/6PjKurIkekfn/KlNi5KAANsd
9a3e9d66-16a7-49e0-89a9-c5a3f18628b6	b6b7ab04-c2b3-4c45-b84f-a9c4f97bb479	certificate	MIIClzCCAX8CBgF14lffCzANBgkqhkiG9w0BAQsFADAPMQ0wCwYDVQQDDARhcHBzMB4XDTIwMTExOTIxMDgzMFoXDTMwMTExOTIxMTAxMFowDzENMAsGA1UEAwwEYXBwczCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAICEXJ2BAZLoKagy38PCNRByJfYuUYTZ+aQfDZieTXSdv16GxKmNlb0sQHI+DSIUbdkF0uWOG6ra0w8k4HPvZv9aKuHcc+5PHFzKxoZCVT1I7B6i3AV3MgdHxIAGELldQ0US/Eh8hZE0byHa0MxlOee8Xn4l1fgF1657huv/OEO9MxOXxsGJ5mDyVqpQy8aoaHFbAdCowi2/TB+P6GfRImT+3T3VtTILdwgtSAdbtyJvnLNcFXXVAdtl6MJO23YAu5Lpr6xMvbeLIbALhSlQyVXJ4ZATB0Gu4jOscWtwAiLmA7eTV2Tg50qCUit2DFlX3u0+OnUguwwfpOk9TcEyNOsCAwEAATANBgkqhkiG9w0BAQsFAAOCAQEAb3nUhKLfRm5kDcDxGg2RfH3jUtuiu+qXeDconjEHByem0v6p/tObaKct3xuk7Hu7nvzwkiKxQNjRAOb4eRAMLXoA1n05YJXmdopl3JUsQ5Vh8b80n6oQ+4Vr6Q0yMpaqds4ikkjbSrMPum/vo6lPEeVwwiTGSDvXT46iVlSED7JZ6BkNaYacFi3hhjlZnf14zuKjRHPBd7Uy4heyLEgPbd7U0ges53JYK1V1MojTJKApz1WKIJNUR/+QZbFFMPhVD69oziPI3tMLaYiFabQswGrryIWkIz1Vc11YfHXcb+jtdCRWEvjlSe3lVwR6fyDbOzg0GLS4QxcXyHueEA7l4A==
4fdda0ba-ecb7-4f46-bb59-e1ee8d988c82	af204def-d5e6-4e68-884d-a5d16f8cf705	kid	dc3aa719-0975-402b-8cb7-d627ea8afc92
047f1dd5-6cb7-404f-b32b-1129fb60bea4	af204def-d5e6-4e68-884d-a5d16f8cf705	priority	100
2eb5cce3-e970-4e9a-bbcc-2b76154191e0	af204def-d5e6-4e68-884d-a5d16f8cf705	secret	yGxtQMcYRMlJI_GRjdmxDA
51ee4def-7b66-4fb1-acbb-c1cc8d5ff6ef	633e5af8-5ce0-410e-8eb0-473974154209	kid	f4df0181-7baf-416e-a5a3-bfb77eb2007b
b226d9b9-4b11-4393-b12f-30d847a5f2f2	633e5af8-5ce0-410e-8eb0-473974154209	secret	wfi776bI422Xu8GcUxeftv-bEheWyBnnIh-TyH5bDUCOqXUMzGZQoRRALAPzph3UJO2rOACFlFB5EXUZGtavxg
5ddf8aa4-b2e6-44ca-9389-4dee82b479c8	633e5af8-5ce0-410e-8eb0-473974154209	priority	100
7fdcb948-3ea9-495f-a792-4391fedbaa7c	633e5af8-5ce0-410e-8eb0-473974154209	algorithm	HS256
d6c08519-1573-4089-9cf3-9215761f940c	43466fdd-c8dc-439e-adff-752e77c60907	host-sending-registration-request-must-match	true
47321465-b9f1-44be-8d34-37b3eb9be366	43466fdd-c8dc-439e-adff-752e77c60907	client-uris-must-match	true
28490767-7e1a-4763-a856-d3e7d9b95c06	93cd1db3-9084-4768-910b-4b41dbd3aebe	allowed-protocol-mapper-types	saml-role-list-mapper
873c124d-d750-4c10-8ff4-941e44d2b572	93cd1db3-9084-4768-910b-4b41dbd3aebe	allowed-protocol-mapper-types	oidc-usermodel-attribute-mapper
b5e2fe39-2d3b-4966-bf3c-a7481eb306d0	93cd1db3-9084-4768-910b-4b41dbd3aebe	allowed-protocol-mapper-types	saml-user-attribute-mapper
40e468f3-806d-429d-b292-1fd54096291d	93cd1db3-9084-4768-910b-4b41dbd3aebe	allowed-protocol-mapper-types	oidc-address-mapper
9f892dcc-969b-4d8d-b59c-ac6ce289ad01	93cd1db3-9084-4768-910b-4b41dbd3aebe	allowed-protocol-mapper-types	oidc-sha256-pairwise-sub-mapper
de89ed01-b430-4f57-a828-c6e607687ef2	93cd1db3-9084-4768-910b-4b41dbd3aebe	allowed-protocol-mapper-types	oidc-full-name-mapper
83702150-f587-49a4-b5d1-abaa8c3624c0	93cd1db3-9084-4768-910b-4b41dbd3aebe	allowed-protocol-mapper-types	oidc-usermodel-property-mapper
fa328e8d-7744-446b-a620-d29c09b9ee44	93cd1db3-9084-4768-910b-4b41dbd3aebe	allowed-protocol-mapper-types	saml-user-property-mapper
941135d4-0684-46bb-80f1-67da3cd295a1	4f93b1da-074f-4c15-93b6-15367fdfb745	allowed-protocol-mapper-types	oidc-full-name-mapper
d39d82ab-f95e-43a8-8c44-15fcc475a560	4f93b1da-074f-4c15-93b6-15367fdfb745	allowed-protocol-mapper-types	oidc-sha256-pairwise-sub-mapper
3751f275-789c-4e8e-8e45-045cdbd83e49	4f93b1da-074f-4c15-93b6-15367fdfb745	allowed-protocol-mapper-types	saml-role-list-mapper
27a28e0f-fbd6-4be7-9700-b09ccd04491b	4f93b1da-074f-4c15-93b6-15367fdfb745	allowed-protocol-mapper-types	oidc-usermodel-property-mapper
27be4911-e4bc-4b01-a6c9-8ee1f9380416	4f93b1da-074f-4c15-93b6-15367fdfb745	allowed-protocol-mapper-types	oidc-usermodel-attribute-mapper
8a767a91-484d-4d31-af29-f52bdeb17ad1	4f93b1da-074f-4c15-93b6-15367fdfb745	allowed-protocol-mapper-types	saml-user-property-mapper
a5289787-d646-4aee-8db6-5fcf6286c5a4	4f93b1da-074f-4c15-93b6-15367fdfb745	allowed-protocol-mapper-types	saml-user-attribute-mapper
01c2d1a1-edcb-4d1f-9365-7426f9c3b18e	4f93b1da-074f-4c15-93b6-15367fdfb745	allowed-protocol-mapper-types	oidc-address-mapper
646cc2ed-413a-4659-a685-26bff9f77522	8943e57f-51ec-4e12-9b7b-070d822327c4	allow-default-scopes	true
a289b739-28a2-46f2-b4ba-f07c6b293f94	1096522e-9c38-4165-8d01-aa0763e15926	max-clients	200
4f9044eb-a2d9-4148-b431-05a318c68a91	9b1c0c05-d6e0-40be-a349-448508cf213a	allow-default-scopes	true
\.


--
-- Data for Name: composite_role; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.composite_role (composite, child_role) FROM stdin;
a0df89ed-8310-4825-a1e5-be61c64c2697	b67c768e-33d7-4eb9-bff4-33eeb602cbe3
a0df89ed-8310-4825-a1e5-be61c64c2697	16d48430-726f-46a6-90aa-7552b7952cf7
a0df89ed-8310-4825-a1e5-be61c64c2697	c4d67cd7-3724-4d0f-bcff-62207521989d
a0df89ed-8310-4825-a1e5-be61c64c2697	3a1f8d79-ca16-4ff2-b53e-ebcd55440753
a0df89ed-8310-4825-a1e5-be61c64c2697	779a221a-26ba-4c7b-a658-1d469c40ed9d
a0df89ed-8310-4825-a1e5-be61c64c2697	546c4983-2426-4846-ab7f-adcf9849bde7
a0df89ed-8310-4825-a1e5-be61c64c2697	dee913ce-7a05-497e-984d-b241a0d956e0
a0df89ed-8310-4825-a1e5-be61c64c2697	2ae7d037-8c7d-413c-9e13-7c969927e6e6
a0df89ed-8310-4825-a1e5-be61c64c2697	43967048-1bb7-4a34-b483-ea141412977f
a0df89ed-8310-4825-a1e5-be61c64c2697	ff517f2b-677b-45bf-b0e6-decffb976a99
a0df89ed-8310-4825-a1e5-be61c64c2697	c911bd13-5ff5-4939-aeb5-9698a8f207c1
a0df89ed-8310-4825-a1e5-be61c64c2697	5f106c3d-94d3-41d8-bb20-55f76a37cbce
a0df89ed-8310-4825-a1e5-be61c64c2697	2155db0e-120f-4383-a707-58e845a98c3b
a0df89ed-8310-4825-a1e5-be61c64c2697	abf2bd32-1fae-42f0-be4b-b08a08f01f79
a0df89ed-8310-4825-a1e5-be61c64c2697	0e03e53d-781e-443a-b4c7-5d2946ef5a83
a0df89ed-8310-4825-a1e5-be61c64c2697	86aed2db-0998-4b10-822f-5dd9813fc149
a0df89ed-8310-4825-a1e5-be61c64c2697	efdabd6b-d766-4f29-ba30-d10b0815e3be
a0df89ed-8310-4825-a1e5-be61c64c2697	eae84876-2fa2-4898-8cd8-e35b1520f530
3a1f8d79-ca16-4ff2-b53e-ebcd55440753	0e03e53d-781e-443a-b4c7-5d2946ef5a83
3a1f8d79-ca16-4ff2-b53e-ebcd55440753	eae84876-2fa2-4898-8cd8-e35b1520f530
779a221a-26ba-4c7b-a658-1d469c40ed9d	86aed2db-0998-4b10-822f-5dd9813fc149
03a27ca6-711a-444d-ba0b-f3a4713dbb94	65e32831-ca1b-4a6e-9f94-5573796495db
e91667ab-8d7e-4be6-9411-55c5dc1bfe6d	df2ccbc9-977b-4e44-874c-e9b9bc6a35c7
a0df89ed-8310-4825-a1e5-be61c64c2697	096204da-7afd-43e2-83df-342d110bb588
a0df89ed-8310-4825-a1e5-be61c64c2697	b4dc1351-8a39-4dbc-86d2-9a5a8d3ae502
a0df89ed-8310-4825-a1e5-be61c64c2697	535c0c76-5e74-4ffa-a310-880443a49337
a0df89ed-8310-4825-a1e5-be61c64c2697	26b8aef4-7d70-4ba3-ab59-1c2972219956
a0df89ed-8310-4825-a1e5-be61c64c2697	abd62ab2-6d45-4b4a-b485-9532496afcc3
a0df89ed-8310-4825-a1e5-be61c64c2697	9a7a5431-b396-4742-a3fc-ba22123335da
a0df89ed-8310-4825-a1e5-be61c64c2697	19d1aea0-ca34-4bda-9150-783c660479ac
a0df89ed-8310-4825-a1e5-be61c64c2697	046ffa78-8a50-4656-b8b3-c3bef583deb6
a0df89ed-8310-4825-a1e5-be61c64c2697	05345eb2-bb7e-4202-b79c-d8625f57bc34
a0df89ed-8310-4825-a1e5-be61c64c2697	09a366ee-944d-419f-b711-c28abdcf9a96
a0df89ed-8310-4825-a1e5-be61c64c2697	2f36b027-d1c9-4c6b-84a5-3460aabd2e83
a0df89ed-8310-4825-a1e5-be61c64c2697	663fb186-27cb-4048-bbe4-0bad27987a83
a0df89ed-8310-4825-a1e5-be61c64c2697	fde57d90-c9e9-4595-9512-341284b15d0c
a0df89ed-8310-4825-a1e5-be61c64c2697	7c35cc5e-a2fe-4878-865a-2e21421bcedc
a0df89ed-8310-4825-a1e5-be61c64c2697	146b5fe2-0d6d-44c5-ae70-e10cc75e63e2
a0df89ed-8310-4825-a1e5-be61c64c2697	7a8ec7ee-b02a-4f2c-9d95-dc66a7cedd1e
a0df89ed-8310-4825-a1e5-be61c64c2697	55cbc27f-6c1c-4e19-9e12-bf69ee7429d0
a0df89ed-8310-4825-a1e5-be61c64c2697	4e426a60-4530-4c0a-881b-58e9fe3d981f
26b8aef4-7d70-4ba3-ab59-1c2972219956	4e426a60-4530-4c0a-881b-58e9fe3d981f
26b8aef4-7d70-4ba3-ab59-1c2972219956	146b5fe2-0d6d-44c5-ae70-e10cc75e63e2
abd62ab2-6d45-4b4a-b485-9532496afcc3	7a8ec7ee-b02a-4f2c-9d95-dc66a7cedd1e
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	92035d36-01d8-47c4-aec4-da378fc9f58b
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	1ebd888c-0dae-4288-8fda-c61c2ea7858f
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	06aa86fa-83e5-4fa3-8f8e-3e9c9b008a4e
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	532e0f3b-f3ec-4a1b-9048-4764f5717ff7
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	f28d81fc-e7ab-4d52-93a3-a020fcf49ff2
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	ab336ea2-08ab-4951-932d-91f543995d28
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	624665ec-849c-49e5-b4f6-fe621ef09934
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	64a71915-4ac1-4924-bbb2-b80102e0f72d
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	8c8fb1f6-ed8f-4e0b-bbdb-cda454cdc466
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	848a3db0-6a09-4465-96bc-999ff2342e4c
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	de3ba3ec-ad2a-47f0-86c3-63f988dad5a0
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	d4d85a88-6a0f-4ce1-b872-13f1c1a43cb4
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	e6e7be38-0b2d-4d67-a55c-f77bbc8627e1
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	3a218ad9-2241-458a-9b17-de203a9a360e
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	427e6bcc-64ba-4e19-8cfa-6cf368c98b9e
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	62dc9b33-5204-4bba-8cf1-c56cf95a41fe
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	00e79e4f-3e8d-49c8-806d-42e74013964f
06aa86fa-83e5-4fa3-8f8e-3e9c9b008a4e	3a218ad9-2241-458a-9b17-de203a9a360e
06aa86fa-83e5-4fa3-8f8e-3e9c9b008a4e	00e79e4f-3e8d-49c8-806d-42e74013964f
532e0f3b-f3ec-4a1b-9048-4764f5717ff7	427e6bcc-64ba-4e19-8cfa-6cf368c98b9e
fbd0725f-04a8-4c91-9275-6ee9881e9881	3799c368-9329-4e9d-ba8c-f2135997f212
333611dd-31bf-4939-acbb-faf9cabd852a	337841ed-b8fb-4cf4-90db-c0e6624509b0
a0df89ed-8310-4825-a1e5-be61c64c2697	dfc9aa2a-8ae0-4fd5-b3c6-107985602122
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	8a1d166d-8c13-4a42-bb1c-76e9e4a9c47b
\.


--
-- Data for Name: credential; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.credential (id, salt, type, user_id, created_date, user_label, secret_data, credential_data, priority) FROM stdin;
47716fcf-fb01-4a96-9975-83e33a15c4ab	\N	password	8b2d671e-a7e0-403b-b39b-375bc549fbb7	1605819923223	\N	{"value":"UxyYT/YS9SHNDDH+P8LXDoVfXGjwwgCT0n/Azjkj1+rJtcV9SNv9sgZelovBepXjJcw4VLpSB8+cfDKo8fKg/g==","salt":"79qU4uyXH7N8NQp2XCe7uA=="}	{"hashIterations":27500,"algorithm":"pbkdf2-sha256"}	10
9b2e1d74-3610-474d-8bc7-e91dbbcf9ffc	\N	password	43f41f0f-25f4-48e9-840a-73497e004fa6	1605820511905	\N	{"value":"eIdGWXSv6qVCUFjjs5cLeFFxJ1hynVNZZRrPi/Dj0TWrQBarm/rukATnkM/hVAzYY4e0K3Z049k0YBWvRQZnHg==","salt":"MY4Q/hmAe1RloI0JqAMJLA=="}	{"hashIterations":27500,"algorithm":"pbkdf2-sha256"}	10
\.


--
-- Data for Name: databasechangelog; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) FROM stdin;
1.0.0.Final-KEYCLOAK-5461	sthorger@redhat.com	META-INF/jpa-changelog-1.0.0.Final.xml	2020-11-19 21:04:56.829971	1	EXECUTED	7:4e70412f24a3f382c82183742ec79317	createTable tableName=APPLICATION_DEFAULT_ROLES; createTable tableName=CLIENT; createTable tableName=CLIENT_SESSION; createTable tableName=CLIENT_SESSION_ROLE; createTable tableName=COMPOSITE_ROLE; createTable tableName=CREDENTIAL; createTable tab...		\N	3.5.4	\N	\N	5819895073
1.0.0.Final-KEYCLOAK-5461	sthorger@redhat.com	META-INF/db2-jpa-changelog-1.0.0.Final.xml	2020-11-19 21:04:56.853867	2	MARK_RAN	7:cb16724583e9675711801c6875114f28	createTable tableName=APPLICATION_DEFAULT_ROLES; createTable tableName=CLIENT; createTable tableName=CLIENT_SESSION; createTable tableName=CLIENT_SESSION_ROLE; createTable tableName=COMPOSITE_ROLE; createTable tableName=CREDENTIAL; createTable tab...		\N	3.5.4	\N	\N	5819895073
1.1.0.Beta1	sthorger@redhat.com	META-INF/jpa-changelog-1.1.0.Beta1.xml	2020-11-19 21:04:57.063524	3	EXECUTED	7:0310eb8ba07cec616460794d42ade0fa	delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION; createTable tableName=CLIENT_ATTRIBUTES; createTable tableName=CLIENT_SESSION_NOTE; createTable tableName=APP_NODE_REGISTRATIONS; addColumn table...		\N	3.5.4	\N	\N	5819895073
1.1.0.Final	sthorger@redhat.com	META-INF/jpa-changelog-1.1.0.Final.xml	2020-11-19 21:04:57.07956	4	EXECUTED	7:5d25857e708c3233ef4439df1f93f012	renameColumn newColumnName=EVENT_TIME, oldColumnName=TIME, tableName=EVENT_ENTITY		\N	3.5.4	\N	\N	5819895073
1.2.0.Beta1	psilva@redhat.com	META-INF/jpa-changelog-1.2.0.Beta1.xml	2020-11-19 21:04:57.658429	5	EXECUTED	7:c7a54a1041d58eb3817a4a883b4d4e84	delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION; createTable tableName=PROTOCOL_MAPPER; createTable tableName=PROTOCOL_MAPPER_CONFIG; createTable tableName=...		\N	3.5.4	\N	\N	5819895073
1.2.0.Beta1	psilva@redhat.com	META-INF/db2-jpa-changelog-1.2.0.Beta1.xml	2020-11-19 21:04:57.666673	6	MARK_RAN	7:2e01012df20974c1c2a605ef8afe25b7	delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION; createTable tableName=PROTOCOL_MAPPER; createTable tableName=PROTOCOL_MAPPER_CONFIG; createTable tableName=...		\N	3.5.4	\N	\N	5819895073
1.2.0.RC1	bburke@redhat.com	META-INF/jpa-changelog-1.2.0.CR1.xml	2020-11-19 21:04:58.259882	7	EXECUTED	7:0f08df48468428e0f30ee59a8ec01a41	delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete tableName=USER_SESSION; createTable tableName=MIGRATION_MODEL; createTable tableName=IDENTITY_P...		\N	3.5.4	\N	\N	5819895073
1.2.0.RC1	bburke@redhat.com	META-INF/db2-jpa-changelog-1.2.0.CR1.xml	2020-11-19 21:04:58.286505	8	MARK_RAN	7:a77ea2ad226b345e7d689d366f185c8c	delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete tableName=USER_SESSION; createTable tableName=MIGRATION_MODEL; createTable tableName=IDENTITY_P...		\N	3.5.4	\N	\N	5819895073
1.2.0.Final	keycloak	META-INF/jpa-changelog-1.2.0.Final.xml	2020-11-19 21:04:58.319922	9	EXECUTED	7:a3377a2059aefbf3b90ebb4c4cc8e2ab	update tableName=CLIENT; update tableName=CLIENT; update tableName=CLIENT		\N	3.5.4	\N	\N	5819895073
1.3.0	bburke@redhat.com	META-INF/jpa-changelog-1.3.0.xml	2020-11-19 21:04:58.959782	10	EXECUTED	7:04c1dbedc2aa3e9756d1a1668e003451	delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete tableName=USER_SESSION; createTable tableName=ADMI...		\N	3.5.4	\N	\N	5819895073
1.4.0	bburke@redhat.com	META-INF/jpa-changelog-1.4.0.xml	2020-11-19 21:04:59.242816	11	EXECUTED	7:36ef39ed560ad07062d956db861042ba	delete tableName=CLIENT_SESSION_AUTH_STATUS; delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete table...		\N	3.5.4	\N	\N	5819895073
1.4.0	bburke@redhat.com	META-INF/db2-jpa-changelog-1.4.0.xml	2020-11-19 21:04:59.2518	12	MARK_RAN	7:d909180b2530479a716d3f9c9eaea3d7	delete tableName=CLIENT_SESSION_AUTH_STATUS; delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete table...		\N	3.5.4	\N	\N	5819895073
1.5.0	bburke@redhat.com	META-INF/jpa-changelog-1.5.0.xml	2020-11-19 21:04:59.285197	13	EXECUTED	7:cf12b04b79bea5152f165eb41f3955f6	delete tableName=CLIENT_SESSION_AUTH_STATUS; delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete table...		\N	3.5.4	\N	\N	5819895073
1.6.1_from15	mposolda@redhat.com	META-INF/jpa-changelog-1.6.1.xml	2020-11-19 21:04:59.435545	14	EXECUTED	7:7e32c8f05c755e8675764e7d5f514509	addColumn tableName=REALM; addColumn tableName=KEYCLOAK_ROLE; addColumn tableName=CLIENT; createTable tableName=OFFLINE_USER_SESSION; createTable tableName=OFFLINE_CLIENT_SESSION; addPrimaryKey constraintName=CONSTRAINT_OFFL_US_SES_PK2, tableName=...		\N	3.5.4	\N	\N	5819895073
1.6.1_from16-pre	mposolda@redhat.com	META-INF/jpa-changelog-1.6.1.xml	2020-11-19 21:04:59.443792	15	MARK_RAN	7:980ba23cc0ec39cab731ce903dd01291	delete tableName=OFFLINE_CLIENT_SESSION; delete tableName=OFFLINE_USER_SESSION		\N	3.5.4	\N	\N	5819895073
1.6.1_from16	mposolda@redhat.com	META-INF/jpa-changelog-1.6.1.xml	2020-11-19 21:04:59.452027	16	MARK_RAN	7:2fa220758991285312eb84f3b4ff5336	dropPrimaryKey constraintName=CONSTRAINT_OFFLINE_US_SES_PK, tableName=OFFLINE_USER_SESSION; dropPrimaryKey constraintName=CONSTRAINT_OFFLINE_CL_SES_PK, tableName=OFFLINE_CLIENT_SESSION; addColumn tableName=OFFLINE_USER_SESSION; update tableName=OF...		\N	3.5.4	\N	\N	5819895073
1.6.1	mposolda@redhat.com	META-INF/jpa-changelog-1.6.1.xml	2020-11-19 21:04:59.460244	17	EXECUTED	7:d41d8cd98f00b204e9800998ecf8427e	empty		\N	3.5.4	\N	\N	5819895073
1.7.0	bburke@redhat.com	META-INF/jpa-changelog-1.7.0.xml	2020-11-19 21:04:59.703337	18	EXECUTED	7:91ace540896df890cc00a0490ee52bbc	createTable tableName=KEYCLOAK_GROUP; createTable tableName=GROUP_ROLE_MAPPING; createTable tableName=GROUP_ATTRIBUTE; createTable tableName=USER_GROUP_MEMBERSHIP; createTable tableName=REALM_DEFAULT_GROUPS; addColumn tableName=IDENTITY_PROVIDER; ...		\N	3.5.4	\N	\N	5819895073
1.8.0	mposolda@redhat.com	META-INF/jpa-changelog-1.8.0.xml	2020-11-19 21:04:59.937114	19	EXECUTED	7:c31d1646dfa2618a9335c00e07f89f24	addColumn tableName=IDENTITY_PROVIDER; createTable tableName=CLIENT_TEMPLATE; createTable tableName=CLIENT_TEMPLATE_ATTRIBUTES; createTable tableName=TEMPLATE_SCOPE_MAPPING; dropNotNullConstraint columnName=CLIENT_ID, tableName=PROTOCOL_MAPPER; ad...		\N	3.5.4	\N	\N	5819895073
1.8.0-2	keycloak	META-INF/jpa-changelog-1.8.0.xml	2020-11-19 21:04:59.952993	20	EXECUTED	7:df8bc21027a4f7cbbb01f6344e89ce07	dropDefaultValue columnName=ALGORITHM, tableName=CREDENTIAL; update tableName=CREDENTIAL		\N	3.5.4	\N	\N	5819895073
authz-3.4.0.CR1-resource-server-pk-change-part1	glavoie@gmail.com	META-INF/jpa-changelog-authz-3.4.0.CR1.xml	2020-11-19 21:05:03.950028	45	EXECUTED	7:6a48ce645a3525488a90fbf76adf3bb3	addColumn tableName=RESOURCE_SERVER_POLICY; addColumn tableName=RESOURCE_SERVER_RESOURCE; addColumn tableName=RESOURCE_SERVER_SCOPE		\N	3.5.4	\N	\N	5819895073
1.8.0	mposolda@redhat.com	META-INF/db2-jpa-changelog-1.8.0.xml	2020-11-19 21:04:59.96202	21	MARK_RAN	7:f987971fe6b37d963bc95fee2b27f8df	addColumn tableName=IDENTITY_PROVIDER; createTable tableName=CLIENT_TEMPLATE; createTable tableName=CLIENT_TEMPLATE_ATTRIBUTES; createTable tableName=TEMPLATE_SCOPE_MAPPING; dropNotNullConstraint columnName=CLIENT_ID, tableName=PROTOCOL_MAPPER; ad...		\N	3.5.4	\N	\N	5819895073
1.8.0-2	keycloak	META-INF/db2-jpa-changelog-1.8.0.xml	2020-11-19 21:04:59.970206	22	MARK_RAN	7:df8bc21027a4f7cbbb01f6344e89ce07	dropDefaultValue columnName=ALGORITHM, tableName=CREDENTIAL; update tableName=CREDENTIAL		\N	3.5.4	\N	\N	5819895073
1.9.0	mposolda@redhat.com	META-INF/jpa-changelog-1.9.0.xml	2020-11-19 21:05:00.037189	23	EXECUTED	7:ed2dc7f799d19ac452cbcda56c929e47	update tableName=REALM; update tableName=REALM; update tableName=REALM; update tableName=REALM; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=REALM; update tableName=REALM; customChange; dr...		\N	3.5.4	\N	\N	5819895073
1.9.1	keycloak	META-INF/jpa-changelog-1.9.1.xml	2020-11-19 21:05:00.052941	24	EXECUTED	7:80b5db88a5dda36ece5f235be8757615	modifyDataType columnName=PRIVATE_KEY, tableName=REALM; modifyDataType columnName=PUBLIC_KEY, tableName=REALM; modifyDataType columnName=CERTIFICATE, tableName=REALM		\N	3.5.4	\N	\N	5819895073
1.9.1	keycloak	META-INF/db2-jpa-changelog-1.9.1.xml	2020-11-19 21:05:00.061364	25	MARK_RAN	7:1437310ed1305a9b93f8848f301726ce	modifyDataType columnName=PRIVATE_KEY, tableName=REALM; modifyDataType columnName=CERTIFICATE, tableName=REALM		\N	3.5.4	\N	\N	5819895073
1.9.2	keycloak	META-INF/jpa-changelog-1.9.2.xml	2020-11-19 21:05:00.461903	26	EXECUTED	7:b82ffb34850fa0836be16deefc6a87c4	createIndex indexName=IDX_USER_EMAIL, tableName=USER_ENTITY; createIndex indexName=IDX_USER_ROLE_MAPPING, tableName=USER_ROLE_MAPPING; createIndex indexName=IDX_USER_GROUP_MAPPING, tableName=USER_GROUP_MEMBERSHIP; createIndex indexName=IDX_USER_CO...		\N	3.5.4	\N	\N	5819895073
authz-2.0.0	psilva@redhat.com	META-INF/jpa-changelog-authz-2.0.0.xml	2020-11-19 21:05:01.090717	27	EXECUTED	7:9cc98082921330d8d9266decdd4bd658	createTable tableName=RESOURCE_SERVER; addPrimaryKey constraintName=CONSTRAINT_FARS, tableName=RESOURCE_SERVER; addUniqueConstraint constraintName=UK_AU8TT6T700S9V50BU18WS5HA6, tableName=RESOURCE_SERVER; createTable tableName=RESOURCE_SERVER_RESOU...		\N	3.5.4	\N	\N	5819895073
authz-2.5.1	psilva@redhat.com	META-INF/jpa-changelog-authz-2.5.1.xml	2020-11-19 21:05:01.099861	28	EXECUTED	7:03d64aeed9cb52b969bd30a7ac0db57e	update tableName=RESOURCE_SERVER_POLICY		\N	3.5.4	\N	\N	5819895073
2.1.0-KEYCLOAK-5461	bburke@redhat.com	META-INF/jpa-changelog-2.1.0.xml	2020-11-19 21:05:01.716205	29	EXECUTED	7:f1f9fd8710399d725b780f463c6b21cd	createTable tableName=BROKER_LINK; createTable tableName=FED_USER_ATTRIBUTE; createTable tableName=FED_USER_CONSENT; createTable tableName=FED_USER_CONSENT_ROLE; createTable tableName=FED_USER_CONSENT_PROT_MAPPER; createTable tableName=FED_USER_CR...		\N	3.5.4	\N	\N	5819895073
2.2.0	bburke@redhat.com	META-INF/jpa-changelog-2.2.0.xml	2020-11-19 21:05:01.799085	30	EXECUTED	7:53188c3eb1107546e6f765835705b6c1	addColumn tableName=ADMIN_EVENT_ENTITY; createTable tableName=CREDENTIAL_ATTRIBUTE; createTable tableName=FED_CREDENTIAL_ATTRIBUTE; modifyDataType columnName=VALUE, tableName=CREDENTIAL; addForeignKeyConstraint baseTableName=FED_CREDENTIAL_ATTRIBU...		\N	3.5.4	\N	\N	5819895073
2.3.0	bburke@redhat.com	META-INF/jpa-changelog-2.3.0.xml	2020-11-19 21:05:01.882709	31	EXECUTED	7:d6e6f3bc57a0c5586737d1351725d4d4	createTable tableName=FEDERATED_USER; addPrimaryKey constraintName=CONSTR_FEDERATED_USER, tableName=FEDERATED_USER; dropDefaultValue columnName=TOTP, tableName=USER_ENTITY; dropColumn columnName=TOTP, tableName=USER_ENTITY; addColumn tableName=IDE...		\N	3.5.4	\N	\N	5819895073
2.4.0	bburke@redhat.com	META-INF/jpa-changelog-2.4.0.xml	2020-11-19 21:05:01.893982	32	EXECUTED	7:454d604fbd755d9df3fd9c6329043aa5	customChange		\N	3.5.4	\N	\N	5819895073
2.5.0	bburke@redhat.com	META-INF/jpa-changelog-2.5.0.xml	2020-11-19 21:05:01.90735	33	EXECUTED	7:57e98a3077e29caf562f7dbf80c72600	customChange; modifyDataType columnName=USER_ID, tableName=OFFLINE_USER_SESSION		\N	3.5.4	\N	\N	5819895073
2.5.0-unicode-oracle	hmlnarik@redhat.com	META-INF/jpa-changelog-2.5.0.xml	2020-11-19 21:05:01.916205	34	MARK_RAN	7:e4c7e8f2256210aee71ddc42f538b57a	modifyDataType columnName=DESCRIPTION, tableName=AUTHENTICATION_FLOW; modifyDataType columnName=DESCRIPTION, tableName=CLIENT_TEMPLATE; modifyDataType columnName=DESCRIPTION, tableName=RESOURCE_SERVER_POLICY; modifyDataType columnName=DESCRIPTION,...		\N	3.5.4	\N	\N	5819895073
2.5.0-unicode-other-dbs	hmlnarik@redhat.com	META-INF/jpa-changelog-2.5.0.xml	2020-11-19 21:05:02.075305	35	EXECUTED	7:09a43c97e49bc626460480aa1379b522	modifyDataType columnName=DESCRIPTION, tableName=AUTHENTICATION_FLOW; modifyDataType columnName=DESCRIPTION, tableName=CLIENT_TEMPLATE; modifyDataType columnName=DESCRIPTION, tableName=RESOURCE_SERVER_POLICY; modifyDataType columnName=DESCRIPTION,...		\N	3.5.4	\N	\N	5819895073
2.5.0-duplicate-email-support	slawomir@dabek.name	META-INF/jpa-changelog-2.5.0.xml	2020-11-19 21:05:02.09089	36	EXECUTED	7:26bfc7c74fefa9126f2ce702fb775553	addColumn tableName=REALM		\N	3.5.4	\N	\N	5819895073
2.5.0-unique-group-names	hmlnarik@redhat.com	META-INF/jpa-changelog-2.5.0.xml	2020-11-19 21:05:02.140981	37	EXECUTED	7:a161e2ae671a9020fff61e996a207377	addUniqueConstraint constraintName=SIBLING_NAMES, tableName=KEYCLOAK_GROUP		\N	3.5.4	\N	\N	5819895073
2.5.1	bburke@redhat.com	META-INF/jpa-changelog-2.5.1.xml	2020-11-19 21:05:02.157501	38	EXECUTED	7:37fc1781855ac5388c494f1442b3f717	addColumn tableName=FED_USER_CONSENT		\N	3.5.4	\N	\N	5819895073
3.0.0	bburke@redhat.com	META-INF/jpa-changelog-3.0.0.xml	2020-11-19 21:05:02.174111	39	EXECUTED	7:13a27db0dae6049541136adad7261d27	addColumn tableName=IDENTITY_PROVIDER		\N	3.5.4	\N	\N	5819895073
3.2.0-fix	keycloak	META-INF/jpa-changelog-3.2.0.xml	2020-11-19 21:05:02.182635	40	MARK_RAN	7:550300617e3b59e8af3a6294df8248a3	addNotNullConstraint columnName=REALM_ID, tableName=CLIENT_INITIAL_ACCESS		\N	3.5.4	\N	\N	5819895073
3.2.0-fix-with-keycloak-5416	keycloak	META-INF/jpa-changelog-3.2.0.xml	2020-11-19 21:05:02.191084	41	MARK_RAN	7:e3a9482b8931481dc2772a5c07c44f17	dropIndex indexName=IDX_CLIENT_INIT_ACC_REALM, tableName=CLIENT_INITIAL_ACCESS; addNotNullConstraint columnName=REALM_ID, tableName=CLIENT_INITIAL_ACCESS; createIndex indexName=IDX_CLIENT_INIT_ACC_REALM, tableName=CLIENT_INITIAL_ACCESS		\N	3.5.4	\N	\N	5819895073
3.2.0-fix-offline-sessions	hmlnarik	META-INF/jpa-changelog-3.2.0.xml	2020-11-19 21:05:02.203116	42	EXECUTED	7:72b07d85a2677cb257edb02b408f332d	customChange		\N	3.5.4	\N	\N	5819895073
3.2.0-fixed	keycloak	META-INF/jpa-changelog-3.2.0.xml	2020-11-19 21:05:03.918753	43	EXECUTED	7:a72a7858967bd414835d19e04d880312	addColumn tableName=REALM; dropPrimaryKey constraintName=CONSTRAINT_OFFL_CL_SES_PK2, tableName=OFFLINE_CLIENT_SESSION; dropColumn columnName=CLIENT_SESSION_ID, tableName=OFFLINE_CLIENT_SESSION; addPrimaryKey constraintName=CONSTRAINT_OFFL_CL_SES_P...		\N	3.5.4	\N	\N	5819895073
3.3.0	keycloak	META-INF/jpa-changelog-3.3.0.xml	2020-11-19 21:05:03.933245	44	EXECUTED	7:94edff7cf9ce179e7e85f0cd78a3cf2c	addColumn tableName=USER_ENTITY		\N	3.5.4	\N	\N	5819895073
authz-3.4.0.CR1-resource-server-pk-change-part2-KEYCLOAK-6095	hmlnarik@redhat.com	META-INF/jpa-changelog-authz-3.4.0.CR1.xml	2020-11-19 21:05:03.961726	46	EXECUTED	7:e64b5dcea7db06077c6e57d3b9e5ca14	customChange		\N	3.5.4	\N	\N	5819895073
authz-3.4.0.CR1-resource-server-pk-change-part3-fixed	glavoie@gmail.com	META-INF/jpa-changelog-authz-3.4.0.CR1.xml	2020-11-19 21:05:03.966808	47	MARK_RAN	7:fd8cf02498f8b1e72496a20afc75178c	dropIndex indexName=IDX_RES_SERV_POL_RES_SERV, tableName=RESOURCE_SERVER_POLICY; dropIndex indexName=IDX_RES_SRV_RES_RES_SRV, tableName=RESOURCE_SERVER_RESOURCE; dropIndex indexName=IDX_RES_SRV_SCOPE_RES_SRV, tableName=RESOURCE_SERVER_SCOPE		\N	3.5.4	\N	\N	5819895073
authz-3.4.0.CR1-resource-server-pk-change-part3-fixed-nodropindex	glavoie@gmail.com	META-INF/jpa-changelog-authz-3.4.0.CR1.xml	2020-11-19 21:05:04.245034	48	EXECUTED	7:542794f25aa2b1fbabb7e577d6646319	addNotNullConstraint columnName=RESOURCE_SERVER_CLIENT_ID, tableName=RESOURCE_SERVER_POLICY; addNotNullConstraint columnName=RESOURCE_SERVER_CLIENT_ID, tableName=RESOURCE_SERVER_RESOURCE; addNotNullConstraint columnName=RESOURCE_SERVER_CLIENT_ID, ...		\N	3.5.4	\N	\N	5819895073
authn-3.4.0.CR1-refresh-token-max-reuse	glavoie@gmail.com	META-INF/jpa-changelog-authz-3.4.0.CR1.xml	2020-11-19 21:05:04.259851	49	EXECUTED	7:edad604c882df12f74941dac3cc6d650	addColumn tableName=REALM		\N	3.5.4	\N	\N	5819895073
3.4.0	keycloak	META-INF/jpa-changelog-3.4.0.xml	2020-11-19 21:05:04.711013	50	EXECUTED	7:0f88b78b7b46480eb92690cbf5e44900	addPrimaryKey constraintName=CONSTRAINT_REALM_DEFAULT_ROLES, tableName=REALM_DEFAULT_ROLES; addPrimaryKey constraintName=CONSTRAINT_COMPOSITE_ROLE, tableName=COMPOSITE_ROLE; addPrimaryKey constraintName=CONSTR_REALM_DEFAULT_GROUPS, tableName=REALM...		\N	3.5.4	\N	\N	5819895073
3.4.0-KEYCLOAK-5230	hmlnarik@redhat.com	META-INF/jpa-changelog-3.4.0.xml	2020-11-19 21:05:05.077445	51	EXECUTED	7:d560e43982611d936457c327f872dd59	createIndex indexName=IDX_FU_ATTRIBUTE, tableName=FED_USER_ATTRIBUTE; createIndex indexName=IDX_FU_CONSENT, tableName=FED_USER_CONSENT; createIndex indexName=IDX_FU_CONSENT_RU, tableName=FED_USER_CONSENT; createIndex indexName=IDX_FU_CREDENTIAL, t...		\N	3.5.4	\N	\N	5819895073
3.4.1	psilva@redhat.com	META-INF/jpa-changelog-3.4.1.xml	2020-11-19 21:05:05.093829	52	EXECUTED	7:c155566c42b4d14ef07059ec3b3bbd8e	modifyDataType columnName=VALUE, tableName=CLIENT_ATTRIBUTES		\N	3.5.4	\N	\N	5819895073
3.4.2	keycloak	META-INF/jpa-changelog-3.4.2.xml	2020-11-19 21:05:05.103342	53	EXECUTED	7:b40376581f12d70f3c89ba8ddf5b7dea	update tableName=REALM		\N	3.5.4	\N	\N	5819895073
3.4.2-KEYCLOAK-5172	mkanis@redhat.com	META-INF/jpa-changelog-3.4.2.xml	2020-11-19 21:05:05.111467	54	EXECUTED	7:a1132cc395f7b95b3646146c2e38f168	update tableName=CLIENT		\N	3.5.4	\N	\N	5819895073
4.0.0-KEYCLOAK-6335	bburke@redhat.com	META-INF/jpa-changelog-4.0.0.xml	2020-11-19 21:05:05.16091	55	EXECUTED	7:d8dc5d89c789105cfa7ca0e82cba60af	createTable tableName=CLIENT_AUTH_FLOW_BINDINGS; addPrimaryKey constraintName=C_CLI_FLOW_BIND, tableName=CLIENT_AUTH_FLOW_BINDINGS		\N	3.5.4	\N	\N	5819895073
4.0.0-CLEANUP-UNUSED-TABLE	bburke@redhat.com	META-INF/jpa-changelog-4.0.0.xml	2020-11-19 21:05:05.177416	56	EXECUTED	7:7822e0165097182e8f653c35517656a3	dropTable tableName=CLIENT_IDENTITY_PROV_MAPPING		\N	3.5.4	\N	\N	5819895073
4.0.0-KEYCLOAK-6228	bburke@redhat.com	META-INF/jpa-changelog-4.0.0.xml	2020-11-19 21:05:05.344883	57	EXECUTED	7:c6538c29b9c9a08f9e9ea2de5c2b6375	dropUniqueConstraint constraintName=UK_JKUWUVD56ONTGSUHOGM8UEWRT, tableName=USER_CONSENT; dropNotNullConstraint columnName=CLIENT_ID, tableName=USER_CONSENT; addColumn tableName=USER_CONSENT; addUniqueConstraint constraintName=UK_JKUWUVD56ONTGSUHO...		\N	3.5.4	\N	\N	5819895073
4.0.0-KEYCLOAK-5579-fixed	mposolda@redhat.com	META-INF/jpa-changelog-4.0.0.xml	2020-11-19 21:05:05.93201	58	EXECUTED	7:6d4893e36de22369cf73bcb051ded875	dropForeignKeyConstraint baseTableName=CLIENT_TEMPLATE_ATTRIBUTES, constraintName=FK_CL_TEMPL_ATTR_TEMPL; renameTable newTableName=CLIENT_SCOPE_ATTRIBUTES, oldTableName=CLIENT_TEMPLATE_ATTRIBUTES; renameColumn newColumnName=SCOPE_ID, oldColumnName...		\N	3.5.4	\N	\N	5819895073
authz-4.0.0.CR1	psilva@redhat.com	META-INF/jpa-changelog-authz-4.0.0.CR1.xml	2020-11-19 21:05:06.188088	59	EXECUTED	7:57960fc0b0f0dd0563ea6f8b2e4a1707	createTable tableName=RESOURCE_SERVER_PERM_TICKET; addPrimaryKey constraintName=CONSTRAINT_FAPMT, tableName=RESOURCE_SERVER_PERM_TICKET; addForeignKeyConstraint baseTableName=RESOURCE_SERVER_PERM_TICKET, constraintName=FK_FRSRHO213XCX4WNKOG82SSPMT...		\N	3.5.4	\N	\N	5819895073
authz-4.0.0.Beta3	psilva@redhat.com	META-INF/jpa-changelog-authz-4.0.0.Beta3.xml	2020-11-19 21:05:06.203746	60	EXECUTED	7:2b4b8bff39944c7097977cc18dbceb3b	addColumn tableName=RESOURCE_SERVER_POLICY; addColumn tableName=RESOURCE_SERVER_PERM_TICKET; addForeignKeyConstraint baseTableName=RESOURCE_SERVER_PERM_TICKET, constraintName=FK_FRSRPO2128CX4WNKOG82SSRFY, referencedTableName=RESOURCE_SERVER_POLICY		\N	3.5.4	\N	\N	5819895073
authz-4.2.0.Final	mhajas@redhat.com	META-INF/jpa-changelog-authz-4.2.0.Final.xml	2020-11-19 21:05:06.22889	61	EXECUTED	7:2aa42a964c59cd5b8ca9822340ba33a8	createTable tableName=RESOURCE_URIS; addForeignKeyConstraint baseTableName=RESOURCE_URIS, constraintName=FK_RESOURCE_SERVER_URIS, referencedTableName=RESOURCE_SERVER_RESOURCE; customChange; dropColumn columnName=URI, tableName=RESOURCE_SERVER_RESO...		\N	3.5.4	\N	\N	5819895073
authz-4.2.0.Final-KEYCLOAK-9944	hmlnarik@redhat.com	META-INF/jpa-changelog-authz-4.2.0.Final.xml	2020-11-19 21:05:06.279173	62	EXECUTED	7:9ac9e58545479929ba23f4a3087a0346	addPrimaryKey constraintName=CONSTRAINT_RESOUR_URIS_PK, tableName=RESOURCE_URIS		\N	3.5.4	\N	\N	5819895073
4.2.0-KEYCLOAK-6313	wadahiro@gmail.com	META-INF/jpa-changelog-4.2.0.xml	2020-11-19 21:05:06.295341	63	EXECUTED	7:14d407c35bc4fe1976867756bcea0c36	addColumn tableName=REQUIRED_ACTION_PROVIDER		\N	3.5.4	\N	\N	5819895073
4.3.0-KEYCLOAK-7984	wadahiro@gmail.com	META-INF/jpa-changelog-4.3.0.xml	2020-11-19 21:05:06.304729	64	EXECUTED	7:241a8030c748c8548e346adee548fa93	update tableName=REQUIRED_ACTION_PROVIDER		\N	3.5.4	\N	\N	5819895073
4.6.0-KEYCLOAK-7950	psilva@redhat.com	META-INF/jpa-changelog-4.6.0.xml	2020-11-19 21:05:06.313041	65	EXECUTED	7:7d3182f65a34fcc61e8d23def037dc3f	update tableName=RESOURCE_SERVER_RESOURCE		\N	3.5.4	\N	\N	5819895073
4.6.0-KEYCLOAK-8377	keycloak	META-INF/jpa-changelog-4.6.0.xml	2020-11-19 21:05:06.429328	66	EXECUTED	7:b30039e00a0b9715d430d1b0636728fa	createTable tableName=ROLE_ATTRIBUTE; addPrimaryKey constraintName=CONSTRAINT_ROLE_ATTRIBUTE_PK, tableName=ROLE_ATTRIBUTE; addForeignKeyConstraint baseTableName=ROLE_ATTRIBUTE, constraintName=FK_ROLE_ATTRIBUTE_ID, referencedTableName=KEYCLOAK_ROLE...		\N	3.5.4	\N	\N	5819895073
4.6.0-KEYCLOAK-8555	gideonray@gmail.com	META-INF/jpa-changelog-4.6.0.xml	2020-11-19 21:05:06.479027	67	EXECUTED	7:3797315ca61d531780f8e6f82f258159	createIndex indexName=IDX_COMPONENT_PROVIDER_TYPE, tableName=COMPONENT		\N	3.5.4	\N	\N	5819895073
4.7.0-KEYCLOAK-1267	sguilhen@redhat.com	META-INF/jpa-changelog-4.7.0.xml	2020-11-19 21:05:06.495636	68	EXECUTED	7:c7aa4c8d9573500c2d347c1941ff0301	addColumn tableName=REALM		\N	3.5.4	\N	\N	5819895073
4.7.0-KEYCLOAK-7275	keycloak	META-INF/jpa-changelog-4.7.0.xml	2020-11-19 21:05:06.546183	69	EXECUTED	7:b207faee394fc074a442ecd42185a5dd	renameColumn newColumnName=CREATED_ON, oldColumnName=LAST_SESSION_REFRESH, tableName=OFFLINE_USER_SESSION; addNotNullConstraint columnName=CREATED_ON, tableName=OFFLINE_USER_SESSION; addColumn tableName=OFFLINE_USER_SESSION; customChange; createIn...		\N	3.5.4	\N	\N	5819895073
4.8.0-KEYCLOAK-8835	sguilhen@redhat.com	META-INF/jpa-changelog-4.8.0.xml	2020-11-19 21:05:06.562407	70	EXECUTED	7:ab9a9762faaba4ddfa35514b212c4922	addNotNullConstraint columnName=SSO_MAX_LIFESPAN_REMEMBER_ME, tableName=REALM; addNotNullConstraint columnName=SSO_IDLE_TIMEOUT_REMEMBER_ME, tableName=REALM		\N	3.5.4	\N	\N	5819895073
authz-7.0.0-KEYCLOAK-10443	psilva@redhat.com	META-INF/jpa-changelog-authz-7.0.0.xml	2020-11-19 21:05:06.578877	71	EXECUTED	7:b9710f74515a6ccb51b72dc0d19df8c4	addColumn tableName=RESOURCE_SERVER		\N	3.5.4	\N	\N	5819895073
8.0.0-adding-credential-columns	keycloak	META-INF/jpa-changelog-8.0.0.xml	2020-11-19 21:05:06.59572	72	EXECUTED	7:ec9707ae4d4f0b7452fee20128083879	addColumn tableName=CREDENTIAL; addColumn tableName=FED_USER_CREDENTIAL		\N	3.5.4	\N	\N	5819895073
8.0.0-updating-credential-data-not-oracle	keycloak	META-INF/jpa-changelog-8.0.0.xml	2020-11-19 21:05:06.608972	73	EXECUTED	7:03b3f4b264c3c68ba082250a80b74216	update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL		\N	3.5.4	\N	\N	5819895073
8.0.0-updating-credential-data-oracle	keycloak	META-INF/jpa-changelog-8.0.0.xml	2020-11-19 21:05:06.612578	74	MARK_RAN	7:64c5728f5ca1f5aa4392217701c4fe23	update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL		\N	3.5.4	\N	\N	5819895073
8.0.0-credential-cleanup-fixed	keycloak	META-INF/jpa-changelog-8.0.0.xml	2020-11-19 21:05:06.647375	75	EXECUTED	7:b48da8c11a3d83ddd6b7d0c8c2219345	dropDefaultValue columnName=COUNTER, tableName=CREDENTIAL; dropDefaultValue columnName=DIGITS, tableName=CREDENTIAL; dropDefaultValue columnName=PERIOD, tableName=CREDENTIAL; dropDefaultValue columnName=ALGORITHM, tableName=CREDENTIAL; dropColumn ...		\N	3.5.4	\N	\N	5819895073
8.0.0-resource-tag-support	keycloak	META-INF/jpa-changelog-8.0.0.xml	2020-11-19 21:05:06.69608	76	EXECUTED	7:a73379915c23bfad3e8f5c6d5c0aa4bd	addColumn tableName=MIGRATION_MODEL; createIndex indexName=IDX_UPDATE_TIME, tableName=MIGRATION_MODEL		\N	3.5.4	\N	\N	5819895073
9.0.0-always-display-client	keycloak	META-INF/jpa-changelog-9.0.0.xml	2020-11-19 21:05:06.712534	77	EXECUTED	7:39e0073779aba192646291aa2332493d	addColumn tableName=CLIENT		\N	3.5.4	\N	\N	5819895073
9.0.0-drop-constraints-for-column-increase	keycloak	META-INF/jpa-changelog-9.0.0.xml	2020-11-19 21:05:06.721219	78	MARK_RAN	7:81f87368f00450799b4bf42ea0b3ec34	dropUniqueConstraint constraintName=UK_FRSR6T700S9V50BU18WS5PMT, tableName=RESOURCE_SERVER_PERM_TICKET; dropUniqueConstraint constraintName=UK_FRSR6T700S9V50BU18WS5HA6, tableName=RESOURCE_SERVER_RESOURCE; dropPrimaryKey constraintName=CONSTRAINT_O...		\N	3.5.4	\N	\N	5819895073
9.0.0-increase-column-size-federated-fk	keycloak	META-INF/jpa-changelog-9.0.0.xml	2020-11-19 21:05:06.82184	79	EXECUTED	7:20b37422abb9fb6571c618148f013a15	modifyDataType columnName=CLIENT_ID, tableName=FED_USER_CONSENT; modifyDataType columnName=CLIENT_REALM_CONSTRAINT, tableName=KEYCLOAK_ROLE; modifyDataType columnName=OWNER, tableName=RESOURCE_SERVER_POLICY; modifyDataType columnName=CLIENT_ID, ta...		\N	3.5.4	\N	\N	5819895073
9.0.0-recreate-constraints-after-column-increase	keycloak	META-INF/jpa-changelog-9.0.0.xml	2020-11-19 21:05:06.830174	80	MARK_RAN	7:1970bb6cfb5ee800736b95ad3fb3c78a	addNotNullConstraint columnName=CLIENT_ID, tableName=OFFLINE_CLIENT_SESSION; addNotNullConstraint columnName=OWNER, tableName=RESOURCE_SERVER_PERM_TICKET; addNotNullConstraint columnName=REQUESTER, tableName=RESOURCE_SERVER_PERM_TICKET; addNotNull...		\N	3.5.4	\N	\N	5819895073
9.0.1-add-index-to-client.client_id	keycloak	META-INF/jpa-changelog-9.0.1.xml	2020-11-19 21:05:06.871348	81	EXECUTED	7:45d9b25fc3b455d522d8dcc10a0f4c80	createIndex indexName=IDX_CLIENT_ID, tableName=CLIENT		\N	3.5.4	\N	\N	5819895073
9.0.1-KEYCLOAK-12579-drop-constraints	keycloak	META-INF/jpa-changelog-9.0.1.xml	2020-11-19 21:05:06.879638	82	MARK_RAN	7:890ae73712bc187a66c2813a724d037f	dropUniqueConstraint constraintName=SIBLING_NAMES, tableName=KEYCLOAK_GROUP		\N	3.5.4	\N	\N	5819895073
9.0.1-KEYCLOAK-12579-add-not-null-constraint	keycloak	META-INF/jpa-changelog-9.0.1.xml	2020-11-19 21:05:06.896315	83	EXECUTED	7:0a211980d27fafe3ff50d19a3a29b538	addNotNullConstraint columnName=PARENT_GROUP, tableName=KEYCLOAK_GROUP		\N	3.5.4	\N	\N	5819895073
9.0.1-KEYCLOAK-12579-recreate-constraints	keycloak	META-INF/jpa-changelog-9.0.1.xml	2020-11-19 21:05:06.904771	84	MARK_RAN	7:a161e2ae671a9020fff61e996a207377	addUniqueConstraint constraintName=SIBLING_NAMES, tableName=KEYCLOAK_GROUP		\N	3.5.4	\N	\N	5819895073
9.0.1-add-index-to-events	keycloak	META-INF/jpa-changelog-9.0.1.xml	2020-11-19 21:05:06.94644	85	EXECUTED	7:01c49302201bdf815b0a18d1f98a55dc	createIndex indexName=IDX_EVENT_TIME, tableName=EVENT_ENTITY		\N	3.5.4	\N	\N	5819895073
\.


--
-- Data for Name: databasechangeloglock; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.databasechangeloglock (id, locked, lockgranted, lockedby) FROM stdin;
1	f	\N	\N
1000	f	\N	\N
1001	f	\N	\N
\.


--
-- Data for Name: default_client_scope; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.default_client_scope (realm_id, scope_id, default_scope) FROM stdin;
master	1c70643e-3d79-45ee-8039-51c774b08f22	f
master	1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1	t
master	7261ff62-c1b7-434b-9512-93a9d2de5fec	t
master	e2276247-2592-4fdf-adff-5e2eb7d6459f	t
master	6e891f5e-cb60-448c-bb74-55796a2d7305	f
master	4c5c75da-4e7b-43f7-ae66-6a16ca87c311	f
master	1683580c-e145-4fa5-986b-1d5715078524	t
master	87ad8125-30a1-4b39-9cf1-c2da2948c00e	t
master	f928b6a6-44d5-423e-b637-12f1c6640abd	f
apps	bffb4877-c9b6-4650-aa25-470e7b40613f	f
apps	22720f21-1408-47a3-a24b-b7a5c0ce35b6	t
apps	e5f5b018-475a-4110-a625-ab398dfa05cc	t
apps	087510cf-bea6-4e2b-bdc9-3ab3819a2e53	t
apps	1ffcdc9a-3500-47e1-a93c-169a6db19f00	f
apps	1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886	f
apps	0fddb81d-0a02-4519-9fd3-530e3639e88d	t
apps	e05868da-77ad-4f01-a50c-dff4c7bb4c51	t
apps	ce6aa081-61c5-4d67-86b7-97cdbfb13667	f
\.


--
-- Data for Name: event_entity; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.event_entity (id, client_id, details_json, error, ip_address, realm_id, session_id, event_time, type, user_id) FROM stdin;
\.


--
-- Data for Name: fed_user_attribute; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fed_user_attribute (id, name, user_id, realm_id, storage_provider_id, value) FROM stdin;
\.


--
-- Data for Name: fed_user_consent; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fed_user_consent (id, client_id, user_id, realm_id, storage_provider_id, created_date, last_updated_date, client_storage_provider, external_client_id) FROM stdin;
\.


--
-- Data for Name: fed_user_consent_cl_scope; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fed_user_consent_cl_scope (user_consent_id, scope_id) FROM stdin;
\.


--
-- Data for Name: fed_user_credential; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fed_user_credential (id, salt, type, created_date, user_id, realm_id, storage_provider_id, user_label, secret_data, credential_data, priority) FROM stdin;
\.


--
-- Data for Name: fed_user_group_membership; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fed_user_group_membership (group_id, user_id, realm_id, storage_provider_id) FROM stdin;
\.


--
-- Data for Name: fed_user_required_action; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fed_user_required_action (required_action, user_id, realm_id, storage_provider_id) FROM stdin;
\.


--
-- Data for Name: fed_user_role_mapping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fed_user_role_mapping (role_id, user_id, realm_id, storage_provider_id) FROM stdin;
\.


--
-- Data for Name: federated_identity; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.federated_identity (identity_provider, realm_id, federated_user_id, federated_username, token, user_id) FROM stdin;
\.


--
-- Data for Name: federated_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.federated_user (id, storage_provider_id, realm_id) FROM stdin;
\.


--
-- Data for Name: group_attribute; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.group_attribute (id, name, value, group_id) FROM stdin;
\.


--
-- Data for Name: group_role_mapping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.group_role_mapping (role_id, group_id) FROM stdin;
\.


--
-- Data for Name: identity_provider; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.identity_provider (internal_id, enabled, provider_alias, provider_id, store_token, authenticate_by_default, realm_id, add_token_role, trust_email, first_broker_login_flow_id, post_broker_login_flow_id, provider_display_name, link_only) FROM stdin;
\.


--
-- Data for Name: identity_provider_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.identity_provider_config (identity_provider_id, value, name) FROM stdin;
\.


--
-- Data for Name: identity_provider_mapper; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.identity_provider_mapper (id, name, idp_alias, idp_mapper_name, realm_id) FROM stdin;
\.


--
-- Data for Name: idp_mapper_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.idp_mapper_config (idp_mapper_id, value, name) FROM stdin;
\.


--
-- Data for Name: keycloak_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.keycloak_group (id, name, parent_group, realm_id) FROM stdin;
\.


--
-- Data for Name: keycloak_role; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.keycloak_role (id, client_realm_constraint, client_role, description, name, realm_id, client, realm) FROM stdin;
a0df89ed-8310-4825-a1e5-be61c64c2697	master	f	${role_admin}	admin	master	\N	master
b67c768e-33d7-4eb9-bff4-33eeb602cbe3	master	f	${role_create-realm}	create-realm	master	\N	master
16d48430-726f-46a6-90aa-7552b7952cf7	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_create-client}	create-client	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
c4d67cd7-3724-4d0f-bcff-62207521989d	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_view-realm}	view-realm	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
3a1f8d79-ca16-4ff2-b53e-ebcd55440753	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_view-users}	view-users	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
779a221a-26ba-4c7b-a658-1d469c40ed9d	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_view-clients}	view-clients	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
546c4983-2426-4846-ab7f-adcf9849bde7	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_view-events}	view-events	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
dee913ce-7a05-497e-984d-b241a0d956e0	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_view-identity-providers}	view-identity-providers	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
2ae7d037-8c7d-413c-9e13-7c969927e6e6	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_view-authorization}	view-authorization	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
43967048-1bb7-4a34-b483-ea141412977f	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_manage-realm}	manage-realm	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
ff517f2b-677b-45bf-b0e6-decffb976a99	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_manage-users}	manage-users	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
c911bd13-5ff5-4939-aeb5-9698a8f207c1	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_manage-clients}	manage-clients	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
5f106c3d-94d3-41d8-bb20-55f76a37cbce	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_manage-events}	manage-events	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
2155db0e-120f-4383-a707-58e845a98c3b	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_manage-identity-providers}	manage-identity-providers	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
abf2bd32-1fae-42f0-be4b-b08a08f01f79	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_manage-authorization}	manage-authorization	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
0e03e53d-781e-443a-b4c7-5d2946ef5a83	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_query-users}	query-users	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
86aed2db-0998-4b10-822f-5dd9813fc149	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_query-clients}	query-clients	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
efdabd6b-d766-4f29-ba30-d10b0815e3be	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_query-realms}	query-realms	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
eae84876-2fa2-4898-8cd8-e35b1520f530	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_query-groups}	query-groups	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
44f22444-e62d-495d-9d6e-33fc5df98fb5	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	t	${role_view-profile}	view-profile	master	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	\N
03a27ca6-711a-444d-ba0b-f3a4713dbb94	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	t	${role_manage-account}	manage-account	master	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	\N
65e32831-ca1b-4a6e-9f94-5573796495db	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	t	${role_manage-account-links}	manage-account-links	master	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	\N
1639f5d2-7b09-4a13-bb38-dbd4a5488478	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	t	${role_view-applications}	view-applications	master	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	\N
df2ccbc9-977b-4e44-874c-e9b9bc6a35c7	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	t	${role_view-consent}	view-consent	master	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	\N
e91667ab-8d7e-4be6-9411-55c5dc1bfe6d	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	t	${role_manage-consent}	manage-consent	master	0d3b5b31-4557-4e16-b3d7-33bf925af7dd	\N
5f772668-d9f6-443c-ac87-3a48f40c8f16	e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	t	${role_read-token}	read-token	master	e9ab5047-4ce0-49d5-bb6e-395ab27c8d5e	\N
096204da-7afd-43e2-83df-342d110bb588	cbb309a2-43a4-45d3-bda7-84e6b87c6393	t	${role_impersonation}	impersonation	master	cbb309a2-43a4-45d3-bda7-84e6b87c6393	\N
8055ea0c-2ec5-49a9-84aa-57f6f07da327	master	f	${role_offline-access}	offline_access	master	\N	master
fa7d4b8d-74e5-42e0-b152-48904f8d2120	master	f	${role_uma_authorization}	uma_authorization	master	\N	master
b4dc1351-8a39-4dbc-86d2-9a5a8d3ae502	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_create-client}	create-client	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
535c0c76-5e74-4ffa-a310-880443a49337	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_view-realm}	view-realm	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
26b8aef4-7d70-4ba3-ab59-1c2972219956	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_view-users}	view-users	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
abd62ab2-6d45-4b4a-b485-9532496afcc3	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_view-clients}	view-clients	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
9a7a5431-b396-4742-a3fc-ba22123335da	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_view-events}	view-events	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
19d1aea0-ca34-4bda-9150-783c660479ac	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_view-identity-providers}	view-identity-providers	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
046ffa78-8a50-4656-b8b3-c3bef583deb6	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_view-authorization}	view-authorization	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
05345eb2-bb7e-4202-b79c-d8625f57bc34	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_manage-realm}	manage-realm	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
09a366ee-944d-419f-b711-c28abdcf9a96	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_manage-users}	manage-users	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
2f36b027-d1c9-4c6b-84a5-3460aabd2e83	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_manage-clients}	manage-clients	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
663fb186-27cb-4048-bbe4-0bad27987a83	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_manage-events}	manage-events	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
fde57d90-c9e9-4595-9512-341284b15d0c	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_manage-identity-providers}	manage-identity-providers	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
7c35cc5e-a2fe-4878-865a-2e21421bcedc	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_manage-authorization}	manage-authorization	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
146b5fe2-0d6d-44c5-ae70-e10cc75e63e2	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_query-users}	query-users	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
7a8ec7ee-b02a-4f2c-9d95-dc66a7cedd1e	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_query-clients}	query-clients	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
55cbc27f-6c1c-4e19-9e12-bf69ee7429d0	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_query-realms}	query-realms	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
4e426a60-4530-4c0a-881b-58e9fe3d981f	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_query-groups}	query-groups	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
5a8cb7e7-a319-4201-a99a-1d88f2f4dbec	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_realm-admin}	realm-admin	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
92035d36-01d8-47c4-aec4-da378fc9f58b	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_create-client}	create-client	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
1ebd888c-0dae-4288-8fda-c61c2ea7858f	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_view-realm}	view-realm	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
06aa86fa-83e5-4fa3-8f8e-3e9c9b008a4e	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_view-users}	view-users	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
532e0f3b-f3ec-4a1b-9048-4764f5717ff7	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_view-clients}	view-clients	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
f28d81fc-e7ab-4d52-93a3-a020fcf49ff2	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_view-events}	view-events	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
ab336ea2-08ab-4951-932d-91f543995d28	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_view-identity-providers}	view-identity-providers	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
624665ec-849c-49e5-b4f6-fe621ef09934	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_view-authorization}	view-authorization	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
64a71915-4ac1-4924-bbb2-b80102e0f72d	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_manage-realm}	manage-realm	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
8c8fb1f6-ed8f-4e0b-bbdb-cda454cdc466	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_manage-users}	manage-users	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
848a3db0-6a09-4465-96bc-999ff2342e4c	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_manage-clients}	manage-clients	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
de3ba3ec-ad2a-47f0-86c3-63f988dad5a0	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_manage-events}	manage-events	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
d4d85a88-6a0f-4ce1-b872-13f1c1a43cb4	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_manage-identity-providers}	manage-identity-providers	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
e6e7be38-0b2d-4d67-a55c-f77bbc8627e1	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_manage-authorization}	manage-authorization	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
3a218ad9-2241-458a-9b17-de203a9a360e	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_query-users}	query-users	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
427e6bcc-64ba-4e19-8cfa-6cf368c98b9e	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_query-clients}	query-clients	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
62dc9b33-5204-4bba-8cf1-c56cf95a41fe	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_query-realms}	query-realms	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
00e79e4f-3e8d-49c8-806d-42e74013964f	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_query-groups}	query-groups	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
8bf05a5c-d17d-4a60-9136-0b586d118c1a	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	t	${role_view-profile}	view-profile	apps	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	\N
fbd0725f-04a8-4c91-9275-6ee9881e9881	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	t	${role_manage-account}	manage-account	apps	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	\N
3799c368-9329-4e9d-ba8c-f2135997f212	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	t	${role_manage-account-links}	manage-account-links	apps	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	\N
4d048887-a697-418c-8e60-e356e972a960	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	t	${role_view-applications}	view-applications	apps	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	\N
337841ed-b8fb-4cf4-90db-c0e6624509b0	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	t	${role_view-consent}	view-consent	apps	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	\N
333611dd-31bf-4939-acbb-faf9cabd852a	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	t	${role_manage-consent}	manage-consent	apps	52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	\N
dfc9aa2a-8ae0-4fd5-b3c6-107985602122	1229b670-54d4-4b05-8abd-7b4a230e8bf6	t	${role_impersonation}	impersonation	master	1229b670-54d4-4b05-8abd-7b4a230e8bf6	\N
8a1d166d-8c13-4a42-bb1c-76e9e4a9c47b	e915762a-6efc-4bd6-96bc-8bb512d4e371	t	${role_impersonation}	impersonation	apps	e915762a-6efc-4bd6-96bc-8bb512d4e371	\N
458c4aaa-1032-46b3-b083-6443dc4c9498	9098959a-5e24-40f1-9b06-7bc629136be8	t	${role_read-token}	read-token	apps	9098959a-5e24-40f1-9b06-7bc629136be8	\N
37849908-4303-45b1-ab4f-90e2e8b23ffa	apps	f	${role_offline-access}	offline_access	apps	\N	apps
d05d0801-3282-4223-a4bc-652c1116792b	apps	f	${role_uma_authorization}	uma_authorization	apps	\N	apps
\.


--
-- Data for Name: migration_model; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.migration_model (id, version, update_time) FROM stdin;
v6mxs	10.0.2	1605819919
\.


--
-- Data for Name: offline_client_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.offline_client_session (user_session_id, client_id, offline_flag, "timestamp", data, client_storage_provider, external_client_id) FROM stdin;
\.


--
-- Data for Name: offline_user_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.offline_user_session (user_session_id, user_id, realm_id, created_on, offline_flag, data, last_session_refresh) FROM stdin;
\.


--
-- Data for Name: policy_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.policy_config (policy_id, name, value) FROM stdin;
\.


--
-- Data for Name: protocol_mapper; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.protocol_mapper (id, name, protocol, protocol_mapper_name, client_id, client_scope_id) FROM stdin;
34330ec2-7fe6-44c2-803f-7b1dc243bf4a	audience resolve	openid-connect	oidc-audience-resolve-mapper	63083332-aa86-44e5-b715-e71acb73f51b	\N
ef75e08d-47fb-40d4-aab9-40cec961aab0	locale	openid-connect	oidc-usermodel-attribute-mapper	2db59d5d-3b62-4da1-a063-c819ae967ff3	\N
e4b1ab5d-f446-433a-adf8-554f0bcd9b84	role list	saml	saml-role-list-mapper	\N	1ffc0efb-dcad-4b41-b5eb-4ab8a35567e1
3115dd5d-ccb1-4984-89eb-b46f9b173d3c	full name	openid-connect	oidc-full-name-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
cd2cd9d0-4ede-41dc-82ed-f84c17a5f771	family name	openid-connect	oidc-usermodel-property-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
31cd10f9-7cf6-4925-a61d-7ef3f9d6be0b	given name	openid-connect	oidc-usermodel-property-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
0a57f68a-0648-4fe2-83e3-976c2333c8df	middle name	openid-connect	oidc-usermodel-attribute-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
8b19ce91-26d6-4078-9ea5-6236c51358c1	nickname	openid-connect	oidc-usermodel-attribute-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
fb399039-cb8b-49f1-910e-8ddf90021677	username	openid-connect	oidc-usermodel-property-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
f15efe70-eba8-450c-a133-955b516d8e56	profile	openid-connect	oidc-usermodel-attribute-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
b26dea29-2221-46fd-913c-884994bfa609	picture	openid-connect	oidc-usermodel-attribute-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
d8c99f65-5733-47a9-8715-662f3f9920a1	website	openid-connect	oidc-usermodel-attribute-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
b26ffaf4-edff-4160-b7db-8b3234e2d804	gender	openid-connect	oidc-usermodel-attribute-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
229ed66d-b2aa-4d41-8a9b-4716f5f7b591	birthdate	openid-connect	oidc-usermodel-attribute-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
6475a0a9-9e13-4d89-9905-1df63828d136	zoneinfo	openid-connect	oidc-usermodel-attribute-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
9ba5ef73-783e-46c1-99e3-5e3a8fc2a156	locale	openid-connect	oidc-usermodel-attribute-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
1feaae39-be71-4c93-b5d9-18ea7be2faa7	updated at	openid-connect	oidc-usermodel-attribute-mapper	\N	7261ff62-c1b7-434b-9512-93a9d2de5fec
e971f8ae-9d20-42b4-aabd-c6a60b58bbf6	email	openid-connect	oidc-usermodel-property-mapper	\N	e2276247-2592-4fdf-adff-5e2eb7d6459f
2a915a92-98b4-4114-8bdd-1521a8a0e072	email verified	openid-connect	oidc-usermodel-property-mapper	\N	e2276247-2592-4fdf-adff-5e2eb7d6459f
524223cb-4c50-48c9-bc76-c7b1b7793dd7	address	openid-connect	oidc-address-mapper	\N	6e891f5e-cb60-448c-bb74-55796a2d7305
b3d73ed4-a047-4e25-a06c-ec75a020e0c6	phone number	openid-connect	oidc-usermodel-attribute-mapper	\N	4c5c75da-4e7b-43f7-ae66-6a16ca87c311
d917fabb-16d0-4193-8593-930a73c552c5	phone number verified	openid-connect	oidc-usermodel-attribute-mapper	\N	4c5c75da-4e7b-43f7-ae66-6a16ca87c311
54eeae3f-18ae-477c-8e27-d9721033ccc5	realm roles	openid-connect	oidc-usermodel-realm-role-mapper	\N	1683580c-e145-4fa5-986b-1d5715078524
0851c3e5-11b2-4a1c-853c-a49b53b41ef3	client roles	openid-connect	oidc-usermodel-client-role-mapper	\N	1683580c-e145-4fa5-986b-1d5715078524
083482f9-4cca-4692-b9ba-b783e2006b35	audience resolve	openid-connect	oidc-audience-resolve-mapper	\N	1683580c-e145-4fa5-986b-1d5715078524
1cb1ab37-b11e-49ec-bbff-7042da5fe73a	allowed web origins	openid-connect	oidc-allowed-origins-mapper	\N	87ad8125-30a1-4b39-9cf1-c2da2948c00e
1df2716f-35b9-47fb-babb-7ef7bcdda9e0	upn	openid-connect	oidc-usermodel-property-mapper	\N	f928b6a6-44d5-423e-b637-12f1c6640abd
29763035-0e78-435e-91a0-0f714f6fb323	groups	openid-connect	oidc-usermodel-realm-role-mapper	\N	f928b6a6-44d5-423e-b637-12f1c6640abd
5584d222-bd67-45ba-9620-36e957bd9011	audience resolve	openid-connect	oidc-audience-resolve-mapper	82e70c4e-3c5a-4637-bc93-c8b8c16c1665	\N
87203714-6e55-40b3-be4a-68b8bc4ddcaa	role list	saml	saml-role-list-mapper	\N	22720f21-1408-47a3-a24b-b7a5c0ce35b6
dc3f26bc-fadc-4ee2-979d-79629cffc04f	full name	openid-connect	oidc-full-name-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
0c84ebc2-86e8-429a-a3ba-ba1833d18797	family name	openid-connect	oidc-usermodel-property-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
171b97db-ecaf-40d0-94d3-41525ba2c008	given name	openid-connect	oidc-usermodel-property-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
d8bbedce-74e5-4f2f-a92a-dcb99e20a7f5	middle name	openid-connect	oidc-usermodel-attribute-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
ae8067f3-0a0e-4805-a994-ff4aa95518d0	nickname	openid-connect	oidc-usermodel-attribute-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
9118a64f-696b-4b76-b7d0-7c139323b8e9	username	openid-connect	oidc-usermodel-property-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
08c3375f-d27b-4cde-a7ae-8768b54d0f8c	profile	openid-connect	oidc-usermodel-attribute-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
638dec66-5e74-40d0-bbf3-9a0185b5a081	picture	openid-connect	oidc-usermodel-attribute-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
fa0ef44d-7a31-41e1-9ea9-c846d17c0e6a	website	openid-connect	oidc-usermodel-attribute-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
cd7b695c-56b1-4abc-9118-84032900e1dd	gender	openid-connect	oidc-usermodel-attribute-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
d0bdb7e9-4773-4277-86b5-08aa9415f3b8	birthdate	openid-connect	oidc-usermodel-attribute-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
7604c962-221b-4893-b7d4-313c5a4fb1a5	zoneinfo	openid-connect	oidc-usermodel-attribute-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
6ef3118d-4192-4987-b22f-7e41d39bb750	locale	openid-connect	oidc-usermodel-attribute-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
dba0b553-dfe8-448d-a3d9-f1b2c8c5f052	updated at	openid-connect	oidc-usermodel-attribute-mapper	\N	e5f5b018-475a-4110-a625-ab398dfa05cc
43b5ac54-ea2c-4fdd-9034-da7ebd46eb4c	email	openid-connect	oidc-usermodel-property-mapper	\N	087510cf-bea6-4e2b-bdc9-3ab3819a2e53
4da03461-c87f-44ac-b557-f12f42fe2360	email verified	openid-connect	oidc-usermodel-property-mapper	\N	087510cf-bea6-4e2b-bdc9-3ab3819a2e53
4c8b9bcc-49ae-4681-b8bc-7b22cb21083c	address	openid-connect	oidc-address-mapper	\N	1ffcdc9a-3500-47e1-a93c-169a6db19f00
cff1c8dc-72f8-4b99-b61b-0b140a34768c	phone number	openid-connect	oidc-usermodel-attribute-mapper	\N	1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886
d5b4f3f4-6b8f-4f5d-8d6b-4280de719592	phone number verified	openid-connect	oidc-usermodel-attribute-mapper	\N	1b6fa3e8-ec8b-45ea-a66a-2e8b7a229886
562446b5-ac43-4ce2-bb22-696fd1db9ed5	realm roles	openid-connect	oidc-usermodel-realm-role-mapper	\N	0fddb81d-0a02-4519-9fd3-530e3639e88d
2d239041-f37c-4d3b-82d5-15cecd90b3da	client roles	openid-connect	oidc-usermodel-client-role-mapper	\N	0fddb81d-0a02-4519-9fd3-530e3639e88d
63f03d9c-0d2c-4ab5-ad4a-ed5d068ef891	audience resolve	openid-connect	oidc-audience-resolve-mapper	\N	0fddb81d-0a02-4519-9fd3-530e3639e88d
42ba0934-1a17-4d47-80de-12a5e3349d9a	allowed web origins	openid-connect	oidc-allowed-origins-mapper	\N	e05868da-77ad-4f01-a50c-dff4c7bb4c51
e26b34d0-285b-4632-b6a6-f318e832e1a2	upn	openid-connect	oidc-usermodel-property-mapper	\N	ce6aa081-61c5-4d67-86b7-97cdbfb13667
07584ba4-9e33-4e1d-b7f4-b0812be2c895	groups	openid-connect	oidc-usermodel-realm-role-mapper	\N	ce6aa081-61c5-4d67-86b7-97cdbfb13667
512bc40b-1e8a-4538-b823-45efe7492be1	locale	openid-connect	oidc-usermodel-attribute-mapper	f17bfceb-76f1-4119-ba55-528255b3d1e7	\N
\.


--
-- Data for Name: protocol_mapper_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.protocol_mapper_config (protocol_mapper_id, value, name) FROM stdin;
ef75e08d-47fb-40d4-aab9-40cec961aab0	true	userinfo.token.claim
ef75e08d-47fb-40d4-aab9-40cec961aab0	locale	user.attribute
ef75e08d-47fb-40d4-aab9-40cec961aab0	true	id.token.claim
ef75e08d-47fb-40d4-aab9-40cec961aab0	true	access.token.claim
ef75e08d-47fb-40d4-aab9-40cec961aab0	locale	claim.name
ef75e08d-47fb-40d4-aab9-40cec961aab0	String	jsonType.label
e4b1ab5d-f446-433a-adf8-554f0bcd9b84	false	single
e4b1ab5d-f446-433a-adf8-554f0bcd9b84	Basic	attribute.nameformat
e4b1ab5d-f446-433a-adf8-554f0bcd9b84	Role	attribute.name
3115dd5d-ccb1-4984-89eb-b46f9b173d3c	true	userinfo.token.claim
3115dd5d-ccb1-4984-89eb-b46f9b173d3c	true	id.token.claim
3115dd5d-ccb1-4984-89eb-b46f9b173d3c	true	access.token.claim
cd2cd9d0-4ede-41dc-82ed-f84c17a5f771	true	userinfo.token.claim
cd2cd9d0-4ede-41dc-82ed-f84c17a5f771	lastName	user.attribute
cd2cd9d0-4ede-41dc-82ed-f84c17a5f771	true	id.token.claim
cd2cd9d0-4ede-41dc-82ed-f84c17a5f771	true	access.token.claim
cd2cd9d0-4ede-41dc-82ed-f84c17a5f771	family_name	claim.name
cd2cd9d0-4ede-41dc-82ed-f84c17a5f771	String	jsonType.label
31cd10f9-7cf6-4925-a61d-7ef3f9d6be0b	true	userinfo.token.claim
31cd10f9-7cf6-4925-a61d-7ef3f9d6be0b	firstName	user.attribute
31cd10f9-7cf6-4925-a61d-7ef3f9d6be0b	true	id.token.claim
31cd10f9-7cf6-4925-a61d-7ef3f9d6be0b	true	access.token.claim
31cd10f9-7cf6-4925-a61d-7ef3f9d6be0b	given_name	claim.name
31cd10f9-7cf6-4925-a61d-7ef3f9d6be0b	String	jsonType.label
0a57f68a-0648-4fe2-83e3-976c2333c8df	true	userinfo.token.claim
0a57f68a-0648-4fe2-83e3-976c2333c8df	middleName	user.attribute
0a57f68a-0648-4fe2-83e3-976c2333c8df	true	id.token.claim
0a57f68a-0648-4fe2-83e3-976c2333c8df	true	access.token.claim
0a57f68a-0648-4fe2-83e3-976c2333c8df	middle_name	claim.name
0a57f68a-0648-4fe2-83e3-976c2333c8df	String	jsonType.label
8b19ce91-26d6-4078-9ea5-6236c51358c1	true	userinfo.token.claim
8b19ce91-26d6-4078-9ea5-6236c51358c1	nickname	user.attribute
8b19ce91-26d6-4078-9ea5-6236c51358c1	true	id.token.claim
8b19ce91-26d6-4078-9ea5-6236c51358c1	true	access.token.claim
8b19ce91-26d6-4078-9ea5-6236c51358c1	nickname	claim.name
8b19ce91-26d6-4078-9ea5-6236c51358c1	String	jsonType.label
fb399039-cb8b-49f1-910e-8ddf90021677	true	userinfo.token.claim
fb399039-cb8b-49f1-910e-8ddf90021677	username	user.attribute
fb399039-cb8b-49f1-910e-8ddf90021677	true	id.token.claim
fb399039-cb8b-49f1-910e-8ddf90021677	true	access.token.claim
fb399039-cb8b-49f1-910e-8ddf90021677	preferred_username	claim.name
fb399039-cb8b-49f1-910e-8ddf90021677	String	jsonType.label
f15efe70-eba8-450c-a133-955b516d8e56	true	userinfo.token.claim
f15efe70-eba8-450c-a133-955b516d8e56	profile	user.attribute
f15efe70-eba8-450c-a133-955b516d8e56	true	id.token.claim
f15efe70-eba8-450c-a133-955b516d8e56	true	access.token.claim
f15efe70-eba8-450c-a133-955b516d8e56	profile	claim.name
f15efe70-eba8-450c-a133-955b516d8e56	String	jsonType.label
b26dea29-2221-46fd-913c-884994bfa609	true	userinfo.token.claim
b26dea29-2221-46fd-913c-884994bfa609	picture	user.attribute
b26dea29-2221-46fd-913c-884994bfa609	true	id.token.claim
b26dea29-2221-46fd-913c-884994bfa609	true	access.token.claim
b26dea29-2221-46fd-913c-884994bfa609	picture	claim.name
b26dea29-2221-46fd-913c-884994bfa609	String	jsonType.label
d8c99f65-5733-47a9-8715-662f3f9920a1	true	userinfo.token.claim
d8c99f65-5733-47a9-8715-662f3f9920a1	website	user.attribute
d8c99f65-5733-47a9-8715-662f3f9920a1	true	id.token.claim
d8c99f65-5733-47a9-8715-662f3f9920a1	true	access.token.claim
d8c99f65-5733-47a9-8715-662f3f9920a1	website	claim.name
d8c99f65-5733-47a9-8715-662f3f9920a1	String	jsonType.label
b26ffaf4-edff-4160-b7db-8b3234e2d804	true	userinfo.token.claim
b26ffaf4-edff-4160-b7db-8b3234e2d804	gender	user.attribute
b26ffaf4-edff-4160-b7db-8b3234e2d804	true	id.token.claim
b26ffaf4-edff-4160-b7db-8b3234e2d804	true	access.token.claim
b26ffaf4-edff-4160-b7db-8b3234e2d804	gender	claim.name
b26ffaf4-edff-4160-b7db-8b3234e2d804	String	jsonType.label
229ed66d-b2aa-4d41-8a9b-4716f5f7b591	true	userinfo.token.claim
229ed66d-b2aa-4d41-8a9b-4716f5f7b591	birthdate	user.attribute
229ed66d-b2aa-4d41-8a9b-4716f5f7b591	true	id.token.claim
229ed66d-b2aa-4d41-8a9b-4716f5f7b591	true	access.token.claim
229ed66d-b2aa-4d41-8a9b-4716f5f7b591	birthdate	claim.name
229ed66d-b2aa-4d41-8a9b-4716f5f7b591	String	jsonType.label
6475a0a9-9e13-4d89-9905-1df63828d136	true	userinfo.token.claim
6475a0a9-9e13-4d89-9905-1df63828d136	zoneinfo	user.attribute
6475a0a9-9e13-4d89-9905-1df63828d136	true	id.token.claim
6475a0a9-9e13-4d89-9905-1df63828d136	true	access.token.claim
6475a0a9-9e13-4d89-9905-1df63828d136	zoneinfo	claim.name
6475a0a9-9e13-4d89-9905-1df63828d136	String	jsonType.label
9ba5ef73-783e-46c1-99e3-5e3a8fc2a156	true	userinfo.token.claim
9ba5ef73-783e-46c1-99e3-5e3a8fc2a156	locale	user.attribute
9ba5ef73-783e-46c1-99e3-5e3a8fc2a156	true	id.token.claim
9ba5ef73-783e-46c1-99e3-5e3a8fc2a156	true	access.token.claim
9ba5ef73-783e-46c1-99e3-5e3a8fc2a156	locale	claim.name
9ba5ef73-783e-46c1-99e3-5e3a8fc2a156	String	jsonType.label
1feaae39-be71-4c93-b5d9-18ea7be2faa7	true	userinfo.token.claim
1feaae39-be71-4c93-b5d9-18ea7be2faa7	updatedAt	user.attribute
1feaae39-be71-4c93-b5d9-18ea7be2faa7	true	id.token.claim
1feaae39-be71-4c93-b5d9-18ea7be2faa7	true	access.token.claim
1feaae39-be71-4c93-b5d9-18ea7be2faa7	updated_at	claim.name
1feaae39-be71-4c93-b5d9-18ea7be2faa7	String	jsonType.label
e971f8ae-9d20-42b4-aabd-c6a60b58bbf6	true	userinfo.token.claim
e971f8ae-9d20-42b4-aabd-c6a60b58bbf6	email	user.attribute
e971f8ae-9d20-42b4-aabd-c6a60b58bbf6	true	id.token.claim
e971f8ae-9d20-42b4-aabd-c6a60b58bbf6	true	access.token.claim
e971f8ae-9d20-42b4-aabd-c6a60b58bbf6	email	claim.name
e971f8ae-9d20-42b4-aabd-c6a60b58bbf6	String	jsonType.label
2a915a92-98b4-4114-8bdd-1521a8a0e072	true	userinfo.token.claim
2a915a92-98b4-4114-8bdd-1521a8a0e072	emailVerified	user.attribute
2a915a92-98b4-4114-8bdd-1521a8a0e072	true	id.token.claim
2a915a92-98b4-4114-8bdd-1521a8a0e072	true	access.token.claim
2a915a92-98b4-4114-8bdd-1521a8a0e072	email_verified	claim.name
2a915a92-98b4-4114-8bdd-1521a8a0e072	boolean	jsonType.label
524223cb-4c50-48c9-bc76-c7b1b7793dd7	formatted	user.attribute.formatted
524223cb-4c50-48c9-bc76-c7b1b7793dd7	country	user.attribute.country
524223cb-4c50-48c9-bc76-c7b1b7793dd7	postal_code	user.attribute.postal_code
524223cb-4c50-48c9-bc76-c7b1b7793dd7	true	userinfo.token.claim
524223cb-4c50-48c9-bc76-c7b1b7793dd7	street	user.attribute.street
524223cb-4c50-48c9-bc76-c7b1b7793dd7	true	id.token.claim
524223cb-4c50-48c9-bc76-c7b1b7793dd7	region	user.attribute.region
524223cb-4c50-48c9-bc76-c7b1b7793dd7	true	access.token.claim
524223cb-4c50-48c9-bc76-c7b1b7793dd7	locality	user.attribute.locality
b3d73ed4-a047-4e25-a06c-ec75a020e0c6	true	userinfo.token.claim
b3d73ed4-a047-4e25-a06c-ec75a020e0c6	phoneNumber	user.attribute
b3d73ed4-a047-4e25-a06c-ec75a020e0c6	true	id.token.claim
b3d73ed4-a047-4e25-a06c-ec75a020e0c6	true	access.token.claim
b3d73ed4-a047-4e25-a06c-ec75a020e0c6	phone_number	claim.name
b3d73ed4-a047-4e25-a06c-ec75a020e0c6	String	jsonType.label
d917fabb-16d0-4193-8593-930a73c552c5	true	userinfo.token.claim
d917fabb-16d0-4193-8593-930a73c552c5	phoneNumberVerified	user.attribute
d917fabb-16d0-4193-8593-930a73c552c5	true	id.token.claim
d917fabb-16d0-4193-8593-930a73c552c5	true	access.token.claim
d917fabb-16d0-4193-8593-930a73c552c5	phone_number_verified	claim.name
d917fabb-16d0-4193-8593-930a73c552c5	boolean	jsonType.label
54eeae3f-18ae-477c-8e27-d9721033ccc5	true	multivalued
54eeae3f-18ae-477c-8e27-d9721033ccc5	foo	user.attribute
54eeae3f-18ae-477c-8e27-d9721033ccc5	true	access.token.claim
54eeae3f-18ae-477c-8e27-d9721033ccc5	realm_access.roles	claim.name
54eeae3f-18ae-477c-8e27-d9721033ccc5	String	jsonType.label
0851c3e5-11b2-4a1c-853c-a49b53b41ef3	true	multivalued
0851c3e5-11b2-4a1c-853c-a49b53b41ef3	foo	user.attribute
0851c3e5-11b2-4a1c-853c-a49b53b41ef3	true	access.token.claim
0851c3e5-11b2-4a1c-853c-a49b53b41ef3	resource_access.${client_id}.roles	claim.name
0851c3e5-11b2-4a1c-853c-a49b53b41ef3	String	jsonType.label
1df2716f-35b9-47fb-babb-7ef7bcdda9e0	true	userinfo.token.claim
1df2716f-35b9-47fb-babb-7ef7bcdda9e0	username	user.attribute
1df2716f-35b9-47fb-babb-7ef7bcdda9e0	true	id.token.claim
1df2716f-35b9-47fb-babb-7ef7bcdda9e0	true	access.token.claim
1df2716f-35b9-47fb-babb-7ef7bcdda9e0	upn	claim.name
1df2716f-35b9-47fb-babb-7ef7bcdda9e0	String	jsonType.label
29763035-0e78-435e-91a0-0f714f6fb323	true	multivalued
29763035-0e78-435e-91a0-0f714f6fb323	foo	user.attribute
29763035-0e78-435e-91a0-0f714f6fb323	true	id.token.claim
29763035-0e78-435e-91a0-0f714f6fb323	true	access.token.claim
29763035-0e78-435e-91a0-0f714f6fb323	groups	claim.name
29763035-0e78-435e-91a0-0f714f6fb323	String	jsonType.label
87203714-6e55-40b3-be4a-68b8bc4ddcaa	false	single
87203714-6e55-40b3-be4a-68b8bc4ddcaa	Basic	attribute.nameformat
87203714-6e55-40b3-be4a-68b8bc4ddcaa	Role	attribute.name
dc3f26bc-fadc-4ee2-979d-79629cffc04f	true	userinfo.token.claim
dc3f26bc-fadc-4ee2-979d-79629cffc04f	true	id.token.claim
dc3f26bc-fadc-4ee2-979d-79629cffc04f	true	access.token.claim
0c84ebc2-86e8-429a-a3ba-ba1833d18797	true	userinfo.token.claim
0c84ebc2-86e8-429a-a3ba-ba1833d18797	lastName	user.attribute
0c84ebc2-86e8-429a-a3ba-ba1833d18797	true	id.token.claim
0c84ebc2-86e8-429a-a3ba-ba1833d18797	true	access.token.claim
0c84ebc2-86e8-429a-a3ba-ba1833d18797	family_name	claim.name
0c84ebc2-86e8-429a-a3ba-ba1833d18797	String	jsonType.label
171b97db-ecaf-40d0-94d3-41525ba2c008	true	userinfo.token.claim
171b97db-ecaf-40d0-94d3-41525ba2c008	firstName	user.attribute
171b97db-ecaf-40d0-94d3-41525ba2c008	true	id.token.claim
171b97db-ecaf-40d0-94d3-41525ba2c008	true	access.token.claim
171b97db-ecaf-40d0-94d3-41525ba2c008	given_name	claim.name
171b97db-ecaf-40d0-94d3-41525ba2c008	String	jsonType.label
d8bbedce-74e5-4f2f-a92a-dcb99e20a7f5	true	userinfo.token.claim
d8bbedce-74e5-4f2f-a92a-dcb99e20a7f5	middleName	user.attribute
d8bbedce-74e5-4f2f-a92a-dcb99e20a7f5	true	id.token.claim
d8bbedce-74e5-4f2f-a92a-dcb99e20a7f5	true	access.token.claim
d8bbedce-74e5-4f2f-a92a-dcb99e20a7f5	middle_name	claim.name
d8bbedce-74e5-4f2f-a92a-dcb99e20a7f5	String	jsonType.label
ae8067f3-0a0e-4805-a994-ff4aa95518d0	true	userinfo.token.claim
ae8067f3-0a0e-4805-a994-ff4aa95518d0	nickname	user.attribute
ae8067f3-0a0e-4805-a994-ff4aa95518d0	true	id.token.claim
ae8067f3-0a0e-4805-a994-ff4aa95518d0	true	access.token.claim
ae8067f3-0a0e-4805-a994-ff4aa95518d0	nickname	claim.name
ae8067f3-0a0e-4805-a994-ff4aa95518d0	String	jsonType.label
9118a64f-696b-4b76-b7d0-7c139323b8e9	true	userinfo.token.claim
9118a64f-696b-4b76-b7d0-7c139323b8e9	username	user.attribute
9118a64f-696b-4b76-b7d0-7c139323b8e9	true	id.token.claim
9118a64f-696b-4b76-b7d0-7c139323b8e9	true	access.token.claim
9118a64f-696b-4b76-b7d0-7c139323b8e9	preferred_username	claim.name
9118a64f-696b-4b76-b7d0-7c139323b8e9	String	jsonType.label
08c3375f-d27b-4cde-a7ae-8768b54d0f8c	true	userinfo.token.claim
08c3375f-d27b-4cde-a7ae-8768b54d0f8c	profile	user.attribute
08c3375f-d27b-4cde-a7ae-8768b54d0f8c	true	id.token.claim
08c3375f-d27b-4cde-a7ae-8768b54d0f8c	true	access.token.claim
08c3375f-d27b-4cde-a7ae-8768b54d0f8c	profile	claim.name
08c3375f-d27b-4cde-a7ae-8768b54d0f8c	String	jsonType.label
638dec66-5e74-40d0-bbf3-9a0185b5a081	true	userinfo.token.claim
638dec66-5e74-40d0-bbf3-9a0185b5a081	picture	user.attribute
638dec66-5e74-40d0-bbf3-9a0185b5a081	true	id.token.claim
638dec66-5e74-40d0-bbf3-9a0185b5a081	true	access.token.claim
638dec66-5e74-40d0-bbf3-9a0185b5a081	picture	claim.name
638dec66-5e74-40d0-bbf3-9a0185b5a081	String	jsonType.label
fa0ef44d-7a31-41e1-9ea9-c846d17c0e6a	true	userinfo.token.claim
fa0ef44d-7a31-41e1-9ea9-c846d17c0e6a	website	user.attribute
fa0ef44d-7a31-41e1-9ea9-c846d17c0e6a	true	id.token.claim
fa0ef44d-7a31-41e1-9ea9-c846d17c0e6a	true	access.token.claim
fa0ef44d-7a31-41e1-9ea9-c846d17c0e6a	website	claim.name
fa0ef44d-7a31-41e1-9ea9-c846d17c0e6a	String	jsonType.label
cd7b695c-56b1-4abc-9118-84032900e1dd	true	userinfo.token.claim
cd7b695c-56b1-4abc-9118-84032900e1dd	gender	user.attribute
cd7b695c-56b1-4abc-9118-84032900e1dd	true	id.token.claim
cd7b695c-56b1-4abc-9118-84032900e1dd	true	access.token.claim
cd7b695c-56b1-4abc-9118-84032900e1dd	gender	claim.name
cd7b695c-56b1-4abc-9118-84032900e1dd	String	jsonType.label
d0bdb7e9-4773-4277-86b5-08aa9415f3b8	true	userinfo.token.claim
d0bdb7e9-4773-4277-86b5-08aa9415f3b8	birthdate	user.attribute
d0bdb7e9-4773-4277-86b5-08aa9415f3b8	true	id.token.claim
d0bdb7e9-4773-4277-86b5-08aa9415f3b8	true	access.token.claim
d0bdb7e9-4773-4277-86b5-08aa9415f3b8	birthdate	claim.name
d0bdb7e9-4773-4277-86b5-08aa9415f3b8	String	jsonType.label
7604c962-221b-4893-b7d4-313c5a4fb1a5	true	userinfo.token.claim
7604c962-221b-4893-b7d4-313c5a4fb1a5	zoneinfo	user.attribute
7604c962-221b-4893-b7d4-313c5a4fb1a5	true	id.token.claim
7604c962-221b-4893-b7d4-313c5a4fb1a5	true	access.token.claim
7604c962-221b-4893-b7d4-313c5a4fb1a5	zoneinfo	claim.name
7604c962-221b-4893-b7d4-313c5a4fb1a5	String	jsonType.label
6ef3118d-4192-4987-b22f-7e41d39bb750	true	userinfo.token.claim
6ef3118d-4192-4987-b22f-7e41d39bb750	locale	user.attribute
6ef3118d-4192-4987-b22f-7e41d39bb750	true	id.token.claim
6ef3118d-4192-4987-b22f-7e41d39bb750	true	access.token.claim
6ef3118d-4192-4987-b22f-7e41d39bb750	locale	claim.name
6ef3118d-4192-4987-b22f-7e41d39bb750	String	jsonType.label
dba0b553-dfe8-448d-a3d9-f1b2c8c5f052	true	userinfo.token.claim
dba0b553-dfe8-448d-a3d9-f1b2c8c5f052	updatedAt	user.attribute
dba0b553-dfe8-448d-a3d9-f1b2c8c5f052	true	id.token.claim
dba0b553-dfe8-448d-a3d9-f1b2c8c5f052	true	access.token.claim
dba0b553-dfe8-448d-a3d9-f1b2c8c5f052	updated_at	claim.name
dba0b553-dfe8-448d-a3d9-f1b2c8c5f052	String	jsonType.label
43b5ac54-ea2c-4fdd-9034-da7ebd46eb4c	true	userinfo.token.claim
43b5ac54-ea2c-4fdd-9034-da7ebd46eb4c	email	user.attribute
43b5ac54-ea2c-4fdd-9034-da7ebd46eb4c	true	id.token.claim
43b5ac54-ea2c-4fdd-9034-da7ebd46eb4c	true	access.token.claim
43b5ac54-ea2c-4fdd-9034-da7ebd46eb4c	email	claim.name
43b5ac54-ea2c-4fdd-9034-da7ebd46eb4c	String	jsonType.label
4da03461-c87f-44ac-b557-f12f42fe2360	true	userinfo.token.claim
4da03461-c87f-44ac-b557-f12f42fe2360	emailVerified	user.attribute
4da03461-c87f-44ac-b557-f12f42fe2360	true	id.token.claim
4da03461-c87f-44ac-b557-f12f42fe2360	true	access.token.claim
4da03461-c87f-44ac-b557-f12f42fe2360	email_verified	claim.name
4da03461-c87f-44ac-b557-f12f42fe2360	boolean	jsonType.label
4c8b9bcc-49ae-4681-b8bc-7b22cb21083c	formatted	user.attribute.formatted
4c8b9bcc-49ae-4681-b8bc-7b22cb21083c	country	user.attribute.country
4c8b9bcc-49ae-4681-b8bc-7b22cb21083c	postal_code	user.attribute.postal_code
4c8b9bcc-49ae-4681-b8bc-7b22cb21083c	true	userinfo.token.claim
4c8b9bcc-49ae-4681-b8bc-7b22cb21083c	street	user.attribute.street
4c8b9bcc-49ae-4681-b8bc-7b22cb21083c	true	id.token.claim
4c8b9bcc-49ae-4681-b8bc-7b22cb21083c	region	user.attribute.region
4c8b9bcc-49ae-4681-b8bc-7b22cb21083c	true	access.token.claim
4c8b9bcc-49ae-4681-b8bc-7b22cb21083c	locality	user.attribute.locality
cff1c8dc-72f8-4b99-b61b-0b140a34768c	true	userinfo.token.claim
cff1c8dc-72f8-4b99-b61b-0b140a34768c	phoneNumber	user.attribute
cff1c8dc-72f8-4b99-b61b-0b140a34768c	true	id.token.claim
cff1c8dc-72f8-4b99-b61b-0b140a34768c	true	access.token.claim
cff1c8dc-72f8-4b99-b61b-0b140a34768c	phone_number	claim.name
cff1c8dc-72f8-4b99-b61b-0b140a34768c	String	jsonType.label
d5b4f3f4-6b8f-4f5d-8d6b-4280de719592	true	userinfo.token.claim
d5b4f3f4-6b8f-4f5d-8d6b-4280de719592	phoneNumberVerified	user.attribute
d5b4f3f4-6b8f-4f5d-8d6b-4280de719592	true	id.token.claim
d5b4f3f4-6b8f-4f5d-8d6b-4280de719592	true	access.token.claim
d5b4f3f4-6b8f-4f5d-8d6b-4280de719592	phone_number_verified	claim.name
d5b4f3f4-6b8f-4f5d-8d6b-4280de719592	boolean	jsonType.label
562446b5-ac43-4ce2-bb22-696fd1db9ed5	true	multivalued
562446b5-ac43-4ce2-bb22-696fd1db9ed5	foo	user.attribute
562446b5-ac43-4ce2-bb22-696fd1db9ed5	true	access.token.claim
562446b5-ac43-4ce2-bb22-696fd1db9ed5	realm_access.roles	claim.name
562446b5-ac43-4ce2-bb22-696fd1db9ed5	String	jsonType.label
2d239041-f37c-4d3b-82d5-15cecd90b3da	true	multivalued
2d239041-f37c-4d3b-82d5-15cecd90b3da	foo	user.attribute
2d239041-f37c-4d3b-82d5-15cecd90b3da	true	access.token.claim
2d239041-f37c-4d3b-82d5-15cecd90b3da	resource_access.${client_id}.roles	claim.name
2d239041-f37c-4d3b-82d5-15cecd90b3da	String	jsonType.label
e26b34d0-285b-4632-b6a6-f318e832e1a2	true	userinfo.token.claim
e26b34d0-285b-4632-b6a6-f318e832e1a2	username	user.attribute
e26b34d0-285b-4632-b6a6-f318e832e1a2	true	id.token.claim
e26b34d0-285b-4632-b6a6-f318e832e1a2	true	access.token.claim
e26b34d0-285b-4632-b6a6-f318e832e1a2	upn	claim.name
e26b34d0-285b-4632-b6a6-f318e832e1a2	String	jsonType.label
07584ba4-9e33-4e1d-b7f4-b0812be2c895	true	multivalued
07584ba4-9e33-4e1d-b7f4-b0812be2c895	foo	user.attribute
07584ba4-9e33-4e1d-b7f4-b0812be2c895	true	id.token.claim
07584ba4-9e33-4e1d-b7f4-b0812be2c895	true	access.token.claim
07584ba4-9e33-4e1d-b7f4-b0812be2c895	groups	claim.name
07584ba4-9e33-4e1d-b7f4-b0812be2c895	String	jsonType.label
512bc40b-1e8a-4538-b823-45efe7492be1	true	userinfo.token.claim
512bc40b-1e8a-4538-b823-45efe7492be1	locale	user.attribute
512bc40b-1e8a-4538-b823-45efe7492be1	true	id.token.claim
512bc40b-1e8a-4538-b823-45efe7492be1	true	access.token.claim
512bc40b-1e8a-4538-b823-45efe7492be1	locale	claim.name
512bc40b-1e8a-4538-b823-45efe7492be1	String	jsonType.label
\.


--
-- Data for Name: realm; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.realm (id, access_code_lifespan, user_action_lifespan, access_token_lifespan, account_theme, admin_theme, email_theme, enabled, events_enabled, events_expiration, login_theme, name, not_before, password_policy, registration_allowed, remember_me, reset_password_allowed, social, ssl_required, sso_idle_timeout, sso_max_lifespan, update_profile_on_soc_login, verify_email, master_admin_client, login_lifespan, internationalization_enabled, default_locale, reg_email_as_username, admin_events_enabled, admin_events_details_enabled, edit_username_allowed, otp_policy_counter, otp_policy_window, otp_policy_period, otp_policy_digits, otp_policy_alg, otp_policy_type, browser_flow, registration_flow, direct_grant_flow, reset_credentials_flow, client_auth_flow, offline_session_idle_timeout, revoke_refresh_token, access_token_life_implicit, login_with_email_allowed, duplicate_emails_allowed, docker_auth_flow, refresh_token_max_reuse, allow_user_managed_access, sso_max_lifespan_remember_me, sso_idle_timeout_remember_me) FROM stdin;
master	60	300	60	\N	\N	\N	t	f	0	\N	master	0	\N	f	f	f	f	EXTERNAL	1800	36000	f	f	cbb309a2-43a4-45d3-bda7-84e6b87c6393	1800	f	\N	f	f	f	f	0	1	30	6	HmacSHA1	totp	671696be-a848-4d42-b76b-12256aeda5bf	833f05e8-0902-4f4c-a2a7-154e3f7619d6	6c5aa605-ea06-4926-816d-63d756e9fcc5	3374da34-b4fd-4870-91dc-110f78513d18	2600c0ce-4c95-46aa-a62c-32cd8af0c837	2592000	f	900	t	f	43bbde40-8833-4e98-82ae-a1c85d4295bd	0	f	0	0
apps	60	300	300	\N	\N	\N	t	f	0	\N	apps	0	\N	f	f	f	f	EXTERNAL	1800	36000	f	f	1229b670-54d4-4b05-8abd-7b4a230e8bf6	1800	f	\N	f	f	f	f	0	1	30	6	HmacSHA1	totp	d552f890-1b2d-4a78-aa6a-0394e5d52a4b	3f738dab-c78b-474c-a2ce-ba9339898a0a	932830d3-2f0b-4678-9250-d52008ec7dc3	bb2d6bb2-2ae8-4d5a-81bf-4b7110190e4f	46cbff58-6904-4b46-8414-05add590377e	2592000	f	900	t	f	f370d353-46cb-4a3d-b074-e3fe18c223fd	0	f	0	0
\.


--
-- Data for Name: realm_attribute; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.realm_attribute (name, value, realm_id) FROM stdin;
_browser_header.contentSecurityPolicyReportOnly		master
_browser_header.xContentTypeOptions	nosniff	master
_browser_header.xRobotsTag	none	master
_browser_header.xFrameOptions	SAMEORIGIN	master
_browser_header.contentSecurityPolicy	frame-src 'self'; frame-ancestors 'self'; object-src 'none';	master
_browser_header.xXSSProtection	1; mode=block	master
_browser_header.strictTransportSecurity	max-age=31536000; includeSubDomains	master
bruteForceProtected	false	master
permanentLockout	false	master
maxFailureWaitSeconds	900	master
minimumQuickLoginWaitSeconds	60	master
waitIncrementSeconds	60	master
quickLoginCheckMilliSeconds	1000	master
maxDeltaTimeSeconds	43200	master
failureFactor	30	master
displayName	Keycloak	master
displayNameHtml	<div class="kc-logo-text"><span>Keycloak</span></div>	master
offlineSessionMaxLifespanEnabled	false	master
offlineSessionMaxLifespan	5184000	master
_browser_header.contentSecurityPolicyReportOnly		apps
_browser_header.xContentTypeOptions	nosniff	apps
_browser_header.xRobotsTag	none	apps
_browser_header.xFrameOptions	SAMEORIGIN	apps
_browser_header.contentSecurityPolicy	frame-src 'self'; frame-ancestors 'self'; object-src 'none';	apps
_browser_header.xXSSProtection	1; mode=block	apps
_browser_header.strictTransportSecurity	max-age=31536000; includeSubDomains	apps
bruteForceProtected	false	apps
permanentLockout	false	apps
maxFailureWaitSeconds	900	apps
minimumQuickLoginWaitSeconds	60	apps
waitIncrementSeconds	60	apps
quickLoginCheckMilliSeconds	1000	apps
maxDeltaTimeSeconds	43200	apps
failureFactor	30	apps
offlineSessionMaxLifespanEnabled	false	apps
offlineSessionMaxLifespan	5184000	apps
actionTokenGeneratedByAdminLifespan	43200	apps
actionTokenGeneratedByUserLifespan	300	apps
webAuthnPolicyRpEntityName	keycloak	apps
webAuthnPolicySignatureAlgorithms	ES256	apps
webAuthnPolicyRpId		apps
webAuthnPolicyAttestationConveyancePreference	not specified	apps
webAuthnPolicyAuthenticatorAttachment	not specified	apps
webAuthnPolicyRequireResidentKey	not specified	apps
webAuthnPolicyUserVerificationRequirement	not specified	apps
webAuthnPolicyCreateTimeout	0	apps
webAuthnPolicyAvoidSameAuthenticatorRegister	false	apps
webAuthnPolicyRpEntityNamePasswordless	keycloak	apps
webAuthnPolicySignatureAlgorithmsPasswordless	ES256	apps
webAuthnPolicyRpIdPasswordless		apps
webAuthnPolicyAttestationConveyancePreferencePasswordless	not specified	apps
webAuthnPolicyAuthenticatorAttachmentPasswordless	not specified	apps
webAuthnPolicyRequireResidentKeyPasswordless	not specified	apps
webAuthnPolicyUserVerificationRequirementPasswordless	not specified	apps
webAuthnPolicyCreateTimeoutPasswordless	0	apps
webAuthnPolicyAvoidSameAuthenticatorRegisterPasswordless	false	apps
\.


--
-- Data for Name: realm_default_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.realm_default_groups (realm_id, group_id) FROM stdin;
\.


--
-- Data for Name: realm_default_roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.realm_default_roles (realm_id, role_id) FROM stdin;
master	8055ea0c-2ec5-49a9-84aa-57f6f07da327
master	fa7d4b8d-74e5-42e0-b152-48904f8d2120
apps	37849908-4303-45b1-ab4f-90e2e8b23ffa
apps	d05d0801-3282-4223-a4bc-652c1116792b
\.


--
-- Data for Name: realm_enabled_event_types; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.realm_enabled_event_types (realm_id, value) FROM stdin;
\.


--
-- Data for Name: realm_events_listeners; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.realm_events_listeners (realm_id, value) FROM stdin;
master	jboss-logging
apps	jboss-logging
\.


--
-- Data for Name: realm_required_credential; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.realm_required_credential (type, form_label, input, secret, realm_id) FROM stdin;
password	password	t	t	master
password	password	t	t	apps
\.


--
-- Data for Name: realm_smtp_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.realm_smtp_config (realm_id, value, name) FROM stdin;
\.


--
-- Data for Name: realm_supported_locales; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.realm_supported_locales (realm_id, value) FROM stdin;
\.


--
-- Data for Name: redirect_uris; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.redirect_uris (client_id, value) FROM stdin;
0d3b5b31-4557-4e16-b3d7-33bf925af7dd	/realms/master/account/*
63083332-aa86-44e5-b715-e71acb73f51b	/realms/master/account/*
2db59d5d-3b62-4da1-a063-c819ae967ff3	/admin/master/console/*
52c26f8f-3ca6-42f8-b63e-6b200fbfc18f	/realms/apps/account/*
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	/realms/apps/account/*
f17bfceb-76f1-4119-ba55-528255b3d1e7	/admin/apps/console/*
cd7f999d-693c-4cb3-aec5-c96712243773	http://localhost:5000/*
\.


--
-- Data for Name: required_action_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.required_action_config (required_action_id, value, name) FROM stdin;
\.


--
-- Data for Name: required_action_provider; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.required_action_provider (id, alias, name, realm_id, enabled, default_action, provider_id, priority) FROM stdin;
dfb0fe7d-6fb0-442c-a179-b6332a5003da	VERIFY_EMAIL	Verify Email	master	t	f	VERIFY_EMAIL	50
40d6a262-ffb8-4fe6-b3cb-21f1e8a7a5de	UPDATE_PROFILE	Update Profile	master	t	f	UPDATE_PROFILE	40
303afa0f-33fa-472f-998b-f2c5ea8ad3bc	CONFIGURE_TOTP	Configure OTP	master	t	f	CONFIGURE_TOTP	10
3bc789c7-6e8f-4240-8c98-31f15b8ebdac	UPDATE_PASSWORD	Update Password	master	t	f	UPDATE_PASSWORD	30
26a44a46-892e-4ced-b2d7-2f3440c54dc9	terms_and_conditions	Terms and Conditions	master	f	f	terms_and_conditions	20
be912d5f-5094-453b-99ac-454a71bc4001	update_user_locale	Update User Locale	master	t	f	update_user_locale	1000
ad5d08d3-e3af-4b13-ab5f-67bd94d421ee	VERIFY_EMAIL	Verify Email	apps	t	f	VERIFY_EMAIL	50
d97eb78d-a35e-44ff-bdfb-22b682c0e1bb	UPDATE_PROFILE	Update Profile	apps	t	f	UPDATE_PROFILE	40
16786fa4-5b96-4bf8-8bc3-3e6fced58a2c	CONFIGURE_TOTP	Configure OTP	apps	t	f	CONFIGURE_TOTP	10
0a6e7e8b-230b-485b-aa82-61229bbc06b3	UPDATE_PASSWORD	Update Password	apps	t	f	UPDATE_PASSWORD	30
254a6da4-e62a-407f-8f3e-91e3c4cff3d6	terms_and_conditions	Terms and Conditions	apps	f	f	terms_and_conditions	20
b93c8cf8-1727-4d13-b463-cb4071df859f	update_user_locale	Update User Locale	apps	t	f	update_user_locale	1000
\.


--
-- Data for Name: resource_attribute; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resource_attribute (id, name, value, resource_id) FROM stdin;
\.


--
-- Data for Name: resource_policy; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resource_policy (resource_id, policy_id) FROM stdin;
\.


--
-- Data for Name: resource_scope; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resource_scope (resource_id, scope_id) FROM stdin;
\.


--
-- Data for Name: resource_server; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resource_server (id, allow_rs_remote_mgmt, policy_enforce_mode, decision_strategy) FROM stdin;
\.


--
-- Data for Name: resource_server_perm_ticket; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resource_server_perm_ticket (id, owner, requester, created_timestamp, granted_timestamp, resource_id, scope_id, resource_server_id, policy_id) FROM stdin;
\.


--
-- Data for Name: resource_server_policy; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resource_server_policy (id, name, description, type, decision_strategy, logic, resource_server_id, owner) FROM stdin;
\.


--
-- Data for Name: resource_server_resource; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resource_server_resource (id, name, type, icon_uri, owner, resource_server_id, owner_managed_access, display_name) FROM stdin;
\.


--
-- Data for Name: resource_server_scope; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resource_server_scope (id, name, icon_uri, resource_server_id, display_name) FROM stdin;
\.


--
-- Data for Name: resource_uris; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resource_uris (resource_id, value) FROM stdin;
\.


--
-- Data for Name: role_attribute; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.role_attribute (id, role_id, name, value) FROM stdin;
\.


--
-- Data for Name: scope_mapping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.scope_mapping (client_id, role_id) FROM stdin;
63083332-aa86-44e5-b715-e71acb73f51b	03a27ca6-711a-444d-ba0b-f3a4713dbb94
82e70c4e-3c5a-4637-bc93-c8b8c16c1665	fbd0725f-04a8-4c91-9275-6ee9881e9881
\.


--
-- Data for Name: scope_policy; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.scope_policy (scope_id, policy_id) FROM stdin;
\.


--
-- Data for Name: user_attribute; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_attribute (name, value, user_id, id) FROM stdin;
\.


--
-- Data for Name: user_consent; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_consent (id, client_id, user_id, created_date, last_updated_date, client_storage_provider, external_client_id) FROM stdin;
\.


--
-- Data for Name: user_consent_client_scope; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_consent_client_scope (user_consent_id, scope_id) FROM stdin;
\.


--
-- Data for Name: user_entity; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_entity (id, email, email_constraint, email_verified, enabled, federation_link, first_name, last_name, realm_id, username, created_timestamp, service_account_client_link, not_before) FROM stdin;
8b2d671e-a7e0-403b-b39b-375bc549fbb7	\N	044661bd-03b0-4d8e-9256-ba2247578b3a	f	t	\N	\N	\N	master	admin	1605819923041	\N	0
43f41f0f-25f4-48e9-840a-73497e004fa6	bbb-visio-user@apps.fr	bbb-visio-user@apps.fr	t	t	\N	BBB	User	apps	bbb-visio-user	1605820441410	\N	0
\.


--
-- Data for Name: user_federation_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_federation_config (user_federation_provider_id, value, name) FROM stdin;
\.


--
-- Data for Name: user_federation_mapper; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_federation_mapper (id, name, federation_provider_id, federation_mapper_type, realm_id) FROM stdin;
\.


--
-- Data for Name: user_federation_mapper_config; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_federation_mapper_config (user_federation_mapper_id, value, name) FROM stdin;
\.


--
-- Data for Name: user_federation_provider; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_federation_provider (id, changed_sync_period, display_name, full_sync_period, last_sync, priority, provider_name, realm_id) FROM stdin;
\.


--
-- Data for Name: user_group_membership; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_group_membership (group_id, user_id) FROM stdin;
\.


--
-- Data for Name: user_required_action; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_required_action (user_id, required_action) FROM stdin;
\.


--
-- Data for Name: user_role_mapping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_role_mapping (role_id, user_id) FROM stdin;
8055ea0c-2ec5-49a9-84aa-57f6f07da327	8b2d671e-a7e0-403b-b39b-375bc549fbb7
03a27ca6-711a-444d-ba0b-f3a4713dbb94	8b2d671e-a7e0-403b-b39b-375bc549fbb7
44f22444-e62d-495d-9d6e-33fc5df98fb5	8b2d671e-a7e0-403b-b39b-375bc549fbb7
fa7d4b8d-74e5-42e0-b152-48904f8d2120	8b2d671e-a7e0-403b-b39b-375bc549fbb7
a0df89ed-8310-4825-a1e5-be61c64c2697	8b2d671e-a7e0-403b-b39b-375bc549fbb7
8bf05a5c-d17d-4a60-9136-0b586d118c1a	43f41f0f-25f4-48e9-840a-73497e004fa6
fbd0725f-04a8-4c91-9275-6ee9881e9881	43f41f0f-25f4-48e9-840a-73497e004fa6
d05d0801-3282-4223-a4bc-652c1116792b	43f41f0f-25f4-48e9-840a-73497e004fa6
37849908-4303-45b1-ab4f-90e2e8b23ffa	43f41f0f-25f4-48e9-840a-73497e004fa6
\.


--
-- Data for Name: user_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_session (id, auth_method, ip_address, last_session_refresh, login_username, realm_id, remember_me, started, user_id, user_session_state, broker_session_id, broker_user_id) FROM stdin;
\.


--
-- Data for Name: user_session_note; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_session_note (user_session, name, value) FROM stdin;
\.


--
-- Data for Name: username_login_failure; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.username_login_failure (realm_id, username, failed_login_not_before, last_failure, last_ip_failure, num_failures) FROM stdin;
\.


--
-- Data for Name: web_origins; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.web_origins (client_id, value) FROM stdin;
2db59d5d-3b62-4da1-a063-c819ae967ff3	+
f17bfceb-76f1-4119-ba55-528255b3d1e7	+
cd7f999d-693c-4cb3-aec5-c96712243773	http://localhost:5000
\.


--
-- Name: username_login_failure CONSTRAINT_17-2; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.username_login_failure
    ADD CONSTRAINT "CONSTRAINT_17-2" PRIMARY KEY (realm_id, username);


--
-- Name: keycloak_role UK_J3RWUVD56ONTGSUHOGM184WW2-2; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.keycloak_role
    ADD CONSTRAINT "UK_J3RWUVD56ONTGSUHOGM184WW2-2" UNIQUE (name, client_realm_constraint);


--
-- Name: client_auth_flow_bindings c_cli_flow_bind; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_auth_flow_bindings
    ADD CONSTRAINT c_cli_flow_bind PRIMARY KEY (client_id, binding_name);


--
-- Name: client_scope_client c_cli_scope_bind; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_scope_client
    ADD CONSTRAINT c_cli_scope_bind PRIMARY KEY (client_id, scope_id);


--
-- Name: client_initial_access cnstr_client_init_acc_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_initial_access
    ADD CONSTRAINT cnstr_client_init_acc_pk PRIMARY KEY (id);


--
-- Name: realm_default_groups con_group_id_def_groups; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_default_groups
    ADD CONSTRAINT con_group_id_def_groups UNIQUE (group_id);


--
-- Name: broker_link constr_broker_link_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.broker_link
    ADD CONSTRAINT constr_broker_link_pk PRIMARY KEY (identity_provider, user_id);


--
-- Name: client_user_session_note constr_cl_usr_ses_note; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_user_session_note
    ADD CONSTRAINT constr_cl_usr_ses_note PRIMARY KEY (client_session, name);


--
-- Name: client_default_roles constr_client_default_roles; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_default_roles
    ADD CONSTRAINT constr_client_default_roles PRIMARY KEY (client_id, role_id);


--
-- Name: component_config constr_component_config_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.component_config
    ADD CONSTRAINT constr_component_config_pk PRIMARY KEY (id);


--
-- Name: component constr_component_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.component
    ADD CONSTRAINT constr_component_pk PRIMARY KEY (id);


--
-- Name: fed_user_required_action constr_fed_required_action; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fed_user_required_action
    ADD CONSTRAINT constr_fed_required_action PRIMARY KEY (required_action, user_id);


--
-- Name: fed_user_attribute constr_fed_user_attr_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fed_user_attribute
    ADD CONSTRAINT constr_fed_user_attr_pk PRIMARY KEY (id);


--
-- Name: fed_user_consent constr_fed_user_consent_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fed_user_consent
    ADD CONSTRAINT constr_fed_user_consent_pk PRIMARY KEY (id);


--
-- Name: fed_user_credential constr_fed_user_cred_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fed_user_credential
    ADD CONSTRAINT constr_fed_user_cred_pk PRIMARY KEY (id);


--
-- Name: fed_user_group_membership constr_fed_user_group; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fed_user_group_membership
    ADD CONSTRAINT constr_fed_user_group PRIMARY KEY (group_id, user_id);


--
-- Name: fed_user_role_mapping constr_fed_user_role; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fed_user_role_mapping
    ADD CONSTRAINT constr_fed_user_role PRIMARY KEY (role_id, user_id);


--
-- Name: federated_user constr_federated_user; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.federated_user
    ADD CONSTRAINT constr_federated_user PRIMARY KEY (id);


--
-- Name: realm_default_groups constr_realm_default_groups; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_default_groups
    ADD CONSTRAINT constr_realm_default_groups PRIMARY KEY (realm_id, group_id);


--
-- Name: realm_enabled_event_types constr_realm_enabl_event_types; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_enabled_event_types
    ADD CONSTRAINT constr_realm_enabl_event_types PRIMARY KEY (realm_id, value);


--
-- Name: realm_events_listeners constr_realm_events_listeners; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_events_listeners
    ADD CONSTRAINT constr_realm_events_listeners PRIMARY KEY (realm_id, value);


--
-- Name: realm_supported_locales constr_realm_supported_locales; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_supported_locales
    ADD CONSTRAINT constr_realm_supported_locales PRIMARY KEY (realm_id, value);


--
-- Name: identity_provider constraint_2b; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.identity_provider
    ADD CONSTRAINT constraint_2b PRIMARY KEY (internal_id);


--
-- Name: client_attributes constraint_3c; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_attributes
    ADD CONSTRAINT constraint_3c PRIMARY KEY (client_id, name);


--
-- Name: event_entity constraint_4; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.event_entity
    ADD CONSTRAINT constraint_4 PRIMARY KEY (id);


--
-- Name: federated_identity constraint_40; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.federated_identity
    ADD CONSTRAINT constraint_40 PRIMARY KEY (identity_provider, user_id);


--
-- Name: realm constraint_4a; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm
    ADD CONSTRAINT constraint_4a PRIMARY KEY (id);


--
-- Name: client_session_role constraint_5; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_session_role
    ADD CONSTRAINT constraint_5 PRIMARY KEY (client_session, role_id);


--
-- Name: user_session constraint_57; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_session
    ADD CONSTRAINT constraint_57 PRIMARY KEY (id);


--
-- Name: user_federation_provider constraint_5c; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_federation_provider
    ADD CONSTRAINT constraint_5c PRIMARY KEY (id);


--
-- Name: client_session_note constraint_5e; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_session_note
    ADD CONSTRAINT constraint_5e PRIMARY KEY (client_session, name);


--
-- Name: client constraint_7; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client
    ADD CONSTRAINT constraint_7 PRIMARY KEY (id);


--
-- Name: client_session constraint_8; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_session
    ADD CONSTRAINT constraint_8 PRIMARY KEY (id);


--
-- Name: scope_mapping constraint_81; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scope_mapping
    ADD CONSTRAINT constraint_81 PRIMARY KEY (client_id, role_id);


--
-- Name: client_node_registrations constraint_84; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_node_registrations
    ADD CONSTRAINT constraint_84 PRIMARY KEY (client_id, name);


--
-- Name: realm_attribute constraint_9; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_attribute
    ADD CONSTRAINT constraint_9 PRIMARY KEY (name, realm_id);


--
-- Name: realm_required_credential constraint_92; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_required_credential
    ADD CONSTRAINT constraint_92 PRIMARY KEY (realm_id, type);


--
-- Name: keycloak_role constraint_a; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.keycloak_role
    ADD CONSTRAINT constraint_a PRIMARY KEY (id);


--
-- Name: admin_event_entity constraint_admin_event_entity; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_event_entity
    ADD CONSTRAINT constraint_admin_event_entity PRIMARY KEY (id);


--
-- Name: authenticator_config_entry constraint_auth_cfg_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.authenticator_config_entry
    ADD CONSTRAINT constraint_auth_cfg_pk PRIMARY KEY (authenticator_id, name);


--
-- Name: authentication_execution constraint_auth_exec_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.authentication_execution
    ADD CONSTRAINT constraint_auth_exec_pk PRIMARY KEY (id);


--
-- Name: authentication_flow constraint_auth_flow_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.authentication_flow
    ADD CONSTRAINT constraint_auth_flow_pk PRIMARY KEY (id);


--
-- Name: authenticator_config constraint_auth_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.authenticator_config
    ADD CONSTRAINT constraint_auth_pk PRIMARY KEY (id);


--
-- Name: client_session_auth_status constraint_auth_status_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_session_auth_status
    ADD CONSTRAINT constraint_auth_status_pk PRIMARY KEY (client_session, authenticator);


--
-- Name: user_role_mapping constraint_c; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_role_mapping
    ADD CONSTRAINT constraint_c PRIMARY KEY (role_id, user_id);


--
-- Name: composite_role constraint_composite_role; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.composite_role
    ADD CONSTRAINT constraint_composite_role PRIMARY KEY (composite, child_role);


--
-- Name: client_session_prot_mapper constraint_cs_pmp_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_session_prot_mapper
    ADD CONSTRAINT constraint_cs_pmp_pk PRIMARY KEY (client_session, protocol_mapper_id);


--
-- Name: identity_provider_config constraint_d; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.identity_provider_config
    ADD CONSTRAINT constraint_d PRIMARY KEY (identity_provider_id, name);


--
-- Name: policy_config constraint_dpc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.policy_config
    ADD CONSTRAINT constraint_dpc PRIMARY KEY (policy_id, name);


--
-- Name: realm_smtp_config constraint_e; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_smtp_config
    ADD CONSTRAINT constraint_e PRIMARY KEY (realm_id, name);


--
-- Name: credential constraint_f; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credential
    ADD CONSTRAINT constraint_f PRIMARY KEY (id);


--
-- Name: user_federation_config constraint_f9; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_federation_config
    ADD CONSTRAINT constraint_f9 PRIMARY KEY (user_federation_provider_id, name);


--
-- Name: resource_server_perm_ticket constraint_fapmt; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_perm_ticket
    ADD CONSTRAINT constraint_fapmt PRIMARY KEY (id);


--
-- Name: resource_server_resource constraint_farsr; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_resource
    ADD CONSTRAINT constraint_farsr PRIMARY KEY (id);


--
-- Name: resource_server_policy constraint_farsrp; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_policy
    ADD CONSTRAINT constraint_farsrp PRIMARY KEY (id);


--
-- Name: associated_policy constraint_farsrpap; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.associated_policy
    ADD CONSTRAINT constraint_farsrpap PRIMARY KEY (policy_id, associated_policy_id);


--
-- Name: resource_policy constraint_farsrpp; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_policy
    ADD CONSTRAINT constraint_farsrpp PRIMARY KEY (resource_id, policy_id);


--
-- Name: resource_server_scope constraint_farsrs; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_scope
    ADD CONSTRAINT constraint_farsrs PRIMARY KEY (id);


--
-- Name: resource_scope constraint_farsrsp; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_scope
    ADD CONSTRAINT constraint_farsrsp PRIMARY KEY (resource_id, scope_id);


--
-- Name: scope_policy constraint_farsrsps; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scope_policy
    ADD CONSTRAINT constraint_farsrsps PRIMARY KEY (scope_id, policy_id);


--
-- Name: user_entity constraint_fb; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_entity
    ADD CONSTRAINT constraint_fb PRIMARY KEY (id);


--
-- Name: user_federation_mapper_config constraint_fedmapper_cfg_pm; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_federation_mapper_config
    ADD CONSTRAINT constraint_fedmapper_cfg_pm PRIMARY KEY (user_federation_mapper_id, name);


--
-- Name: user_federation_mapper constraint_fedmapperpm; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_federation_mapper
    ADD CONSTRAINT constraint_fedmapperpm PRIMARY KEY (id);


--
-- Name: fed_user_consent_cl_scope constraint_fgrntcsnt_clsc_pm; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fed_user_consent_cl_scope
    ADD CONSTRAINT constraint_fgrntcsnt_clsc_pm PRIMARY KEY (user_consent_id, scope_id);


--
-- Name: user_consent_client_scope constraint_grntcsnt_clsc_pm; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_consent_client_scope
    ADD CONSTRAINT constraint_grntcsnt_clsc_pm PRIMARY KEY (user_consent_id, scope_id);


--
-- Name: user_consent constraint_grntcsnt_pm; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_consent
    ADD CONSTRAINT constraint_grntcsnt_pm PRIMARY KEY (id);


--
-- Name: keycloak_group constraint_group; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.keycloak_group
    ADD CONSTRAINT constraint_group PRIMARY KEY (id);


--
-- Name: group_attribute constraint_group_attribute_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_attribute
    ADD CONSTRAINT constraint_group_attribute_pk PRIMARY KEY (id);


--
-- Name: group_role_mapping constraint_group_role; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_role_mapping
    ADD CONSTRAINT constraint_group_role PRIMARY KEY (role_id, group_id);


--
-- Name: identity_provider_mapper constraint_idpm; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.identity_provider_mapper
    ADD CONSTRAINT constraint_idpm PRIMARY KEY (id);


--
-- Name: idp_mapper_config constraint_idpmconfig; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.idp_mapper_config
    ADD CONSTRAINT constraint_idpmconfig PRIMARY KEY (idp_mapper_id, name);


--
-- Name: migration_model constraint_migmod; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.migration_model
    ADD CONSTRAINT constraint_migmod PRIMARY KEY (id);


--
-- Name: offline_client_session constraint_offl_cl_ses_pk3; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.offline_client_session
    ADD CONSTRAINT constraint_offl_cl_ses_pk3 PRIMARY KEY (user_session_id, client_id, client_storage_provider, external_client_id, offline_flag);


--
-- Name: offline_user_session constraint_offl_us_ses_pk2; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.offline_user_session
    ADD CONSTRAINT constraint_offl_us_ses_pk2 PRIMARY KEY (user_session_id, offline_flag);


--
-- Name: protocol_mapper constraint_pcm; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.protocol_mapper
    ADD CONSTRAINT constraint_pcm PRIMARY KEY (id);


--
-- Name: protocol_mapper_config constraint_pmconfig; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.protocol_mapper_config
    ADD CONSTRAINT constraint_pmconfig PRIMARY KEY (protocol_mapper_id, name);


--
-- Name: realm_default_roles constraint_realm_default_roles; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_default_roles
    ADD CONSTRAINT constraint_realm_default_roles PRIMARY KEY (realm_id, role_id);


--
-- Name: redirect_uris constraint_redirect_uris; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.redirect_uris
    ADD CONSTRAINT constraint_redirect_uris PRIMARY KEY (client_id, value);


--
-- Name: required_action_config constraint_req_act_cfg_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.required_action_config
    ADD CONSTRAINT constraint_req_act_cfg_pk PRIMARY KEY (required_action_id, name);


--
-- Name: required_action_provider constraint_req_act_prv_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.required_action_provider
    ADD CONSTRAINT constraint_req_act_prv_pk PRIMARY KEY (id);


--
-- Name: user_required_action constraint_required_action; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_required_action
    ADD CONSTRAINT constraint_required_action PRIMARY KEY (required_action, user_id);


--
-- Name: resource_uris constraint_resour_uris_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_uris
    ADD CONSTRAINT constraint_resour_uris_pk PRIMARY KEY (resource_id, value);


--
-- Name: role_attribute constraint_role_attribute_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_attribute
    ADD CONSTRAINT constraint_role_attribute_pk PRIMARY KEY (id);


--
-- Name: user_attribute constraint_user_attribute_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_attribute
    ADD CONSTRAINT constraint_user_attribute_pk PRIMARY KEY (id);


--
-- Name: user_group_membership constraint_user_group; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_group_membership
    ADD CONSTRAINT constraint_user_group PRIMARY KEY (group_id, user_id);


--
-- Name: user_session_note constraint_usn_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_session_note
    ADD CONSTRAINT constraint_usn_pk PRIMARY KEY (user_session, name);


--
-- Name: web_origins constraint_web_origins; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.web_origins
    ADD CONSTRAINT constraint_web_origins PRIMARY KEY (client_id, value);


--
-- Name: client_scope_attributes pk_cl_tmpl_attr; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_scope_attributes
    ADD CONSTRAINT pk_cl_tmpl_attr PRIMARY KEY (scope_id, name);


--
-- Name: client_scope pk_cli_template; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_scope
    ADD CONSTRAINT pk_cli_template PRIMARY KEY (id);


--
-- Name: databasechangeloglock pk_databasechangeloglock; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.databasechangeloglock
    ADD CONSTRAINT pk_databasechangeloglock PRIMARY KEY (id);


--
-- Name: resource_server pk_resource_server; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server
    ADD CONSTRAINT pk_resource_server PRIMARY KEY (id);


--
-- Name: client_scope_role_mapping pk_template_scope; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_scope_role_mapping
    ADD CONSTRAINT pk_template_scope PRIMARY KEY (scope_id, role_id);


--
-- Name: default_client_scope r_def_cli_scope_bind; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.default_client_scope
    ADD CONSTRAINT r_def_cli_scope_bind PRIMARY KEY (realm_id, scope_id);


--
-- Name: resource_attribute res_attr_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_attribute
    ADD CONSTRAINT res_attr_pk PRIMARY KEY (id);


--
-- Name: keycloak_group sibling_names; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.keycloak_group
    ADD CONSTRAINT sibling_names UNIQUE (realm_id, parent_group, name);


--
-- Name: identity_provider uk_2daelwnibji49avxsrtuf6xj33; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.identity_provider
    ADD CONSTRAINT uk_2daelwnibji49avxsrtuf6xj33 UNIQUE (provider_alias, realm_id);


--
-- Name: client_default_roles uk_8aelwnibji49avxsrtuf6xjow; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_default_roles
    ADD CONSTRAINT uk_8aelwnibji49avxsrtuf6xjow UNIQUE (role_id);


--
-- Name: client uk_b71cjlbenv945rb6gcon438at; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client
    ADD CONSTRAINT uk_b71cjlbenv945rb6gcon438at UNIQUE (realm_id, client_id);


--
-- Name: client_scope uk_cli_scope; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_scope
    ADD CONSTRAINT uk_cli_scope UNIQUE (realm_id, name);


--
-- Name: user_entity uk_dykn684sl8up1crfei6eckhd7; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_entity
    ADD CONSTRAINT uk_dykn684sl8up1crfei6eckhd7 UNIQUE (realm_id, email_constraint);


--
-- Name: resource_server_resource uk_frsr6t700s9v50bu18ws5ha6; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_resource
    ADD CONSTRAINT uk_frsr6t700s9v50bu18ws5ha6 UNIQUE (name, owner, resource_server_id);


--
-- Name: resource_server_perm_ticket uk_frsr6t700s9v50bu18ws5pmt; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_perm_ticket
    ADD CONSTRAINT uk_frsr6t700s9v50bu18ws5pmt UNIQUE (owner, requester, resource_server_id, resource_id, scope_id);


--
-- Name: resource_server_policy uk_frsrpt700s9v50bu18ws5ha6; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_policy
    ADD CONSTRAINT uk_frsrpt700s9v50bu18ws5ha6 UNIQUE (name, resource_server_id);


--
-- Name: resource_server_scope uk_frsrst700s9v50bu18ws5ha6; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_scope
    ADD CONSTRAINT uk_frsrst700s9v50bu18ws5ha6 UNIQUE (name, resource_server_id);


--
-- Name: realm_default_roles uk_h4wpd7w4hsoolni3h0sw7btje; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_default_roles
    ADD CONSTRAINT uk_h4wpd7w4hsoolni3h0sw7btje UNIQUE (role_id);


--
-- Name: user_consent uk_jkuwuvd56ontgsuhogm8uewrt; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_consent
    ADD CONSTRAINT uk_jkuwuvd56ontgsuhogm8uewrt UNIQUE (client_id, client_storage_provider, external_client_id, user_id);


--
-- Name: realm uk_orvsdmla56612eaefiq6wl5oi; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm
    ADD CONSTRAINT uk_orvsdmla56612eaefiq6wl5oi UNIQUE (name);


--
-- Name: user_entity uk_ru8tt6t700s9v50bu18ws5ha6; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_entity
    ADD CONSTRAINT uk_ru8tt6t700s9v50bu18ws5ha6 UNIQUE (realm_id, username);


--
-- Name: idx_assoc_pol_assoc_pol_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_assoc_pol_assoc_pol_id ON public.associated_policy USING btree (associated_policy_id);


--
-- Name: idx_auth_config_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_auth_config_realm ON public.authenticator_config USING btree (realm_id);


--
-- Name: idx_auth_exec_flow; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_auth_exec_flow ON public.authentication_execution USING btree (flow_id);


--
-- Name: idx_auth_exec_realm_flow; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_auth_exec_realm_flow ON public.authentication_execution USING btree (realm_id, flow_id);


--
-- Name: idx_auth_flow_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_auth_flow_realm ON public.authentication_flow USING btree (realm_id);


--
-- Name: idx_cl_clscope; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cl_clscope ON public.client_scope_client USING btree (scope_id);


--
-- Name: idx_client_def_roles_client; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_client_def_roles_client ON public.client_default_roles USING btree (client_id);


--
-- Name: idx_client_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_client_id ON public.client USING btree (client_id);


--
-- Name: idx_client_init_acc_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_client_init_acc_realm ON public.client_initial_access USING btree (realm_id);


--
-- Name: idx_client_session_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_client_session_session ON public.client_session USING btree (session_id);


--
-- Name: idx_clscope_attrs; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_clscope_attrs ON public.client_scope_attributes USING btree (scope_id);


--
-- Name: idx_clscope_cl; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_clscope_cl ON public.client_scope_client USING btree (client_id);


--
-- Name: idx_clscope_protmap; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_clscope_protmap ON public.protocol_mapper USING btree (client_scope_id);


--
-- Name: idx_clscope_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_clscope_role ON public.client_scope_role_mapping USING btree (scope_id);


--
-- Name: idx_compo_config_compo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_compo_config_compo ON public.component_config USING btree (component_id);


--
-- Name: idx_component_provider_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_component_provider_type ON public.component USING btree (provider_type);


--
-- Name: idx_component_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_component_realm ON public.component USING btree (realm_id);


--
-- Name: idx_composite; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_composite ON public.composite_role USING btree (composite);


--
-- Name: idx_composite_child; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_composite_child ON public.composite_role USING btree (child_role);


--
-- Name: idx_defcls_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_defcls_realm ON public.default_client_scope USING btree (realm_id);


--
-- Name: idx_defcls_scope; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_defcls_scope ON public.default_client_scope USING btree (scope_id);


--
-- Name: idx_event_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_event_time ON public.event_entity USING btree (realm_id, event_time);


--
-- Name: idx_fedidentity_feduser; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fedidentity_feduser ON public.federated_identity USING btree (federated_user_id);


--
-- Name: idx_fedidentity_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fedidentity_user ON public.federated_identity USING btree (user_id);


--
-- Name: idx_fu_attribute; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_attribute ON public.fed_user_attribute USING btree (user_id, realm_id, name);


--
-- Name: idx_fu_cnsnt_ext; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_cnsnt_ext ON public.fed_user_consent USING btree (user_id, client_storage_provider, external_client_id);


--
-- Name: idx_fu_consent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_consent ON public.fed_user_consent USING btree (user_id, client_id);


--
-- Name: idx_fu_consent_ru; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_consent_ru ON public.fed_user_consent USING btree (realm_id, user_id);


--
-- Name: idx_fu_credential; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_credential ON public.fed_user_credential USING btree (user_id, type);


--
-- Name: idx_fu_credential_ru; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_credential_ru ON public.fed_user_credential USING btree (realm_id, user_id);


--
-- Name: idx_fu_group_membership; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_group_membership ON public.fed_user_group_membership USING btree (user_id, group_id);


--
-- Name: idx_fu_group_membership_ru; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_group_membership_ru ON public.fed_user_group_membership USING btree (realm_id, user_id);


--
-- Name: idx_fu_required_action; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_required_action ON public.fed_user_required_action USING btree (user_id, required_action);


--
-- Name: idx_fu_required_action_ru; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_required_action_ru ON public.fed_user_required_action USING btree (realm_id, user_id);


--
-- Name: idx_fu_role_mapping; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_role_mapping ON public.fed_user_role_mapping USING btree (user_id, role_id);


--
-- Name: idx_fu_role_mapping_ru; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fu_role_mapping_ru ON public.fed_user_role_mapping USING btree (realm_id, user_id);


--
-- Name: idx_group_attr_group; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_group_attr_group ON public.group_attribute USING btree (group_id);


--
-- Name: idx_group_role_mapp_group; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_group_role_mapp_group ON public.group_role_mapping USING btree (group_id);


--
-- Name: idx_id_prov_mapp_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_id_prov_mapp_realm ON public.identity_provider_mapper USING btree (realm_id);


--
-- Name: idx_ident_prov_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ident_prov_realm ON public.identity_provider USING btree (realm_id);


--
-- Name: idx_keycloak_role_client; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_keycloak_role_client ON public.keycloak_role USING btree (client);


--
-- Name: idx_keycloak_role_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_keycloak_role_realm ON public.keycloak_role USING btree (realm);


--
-- Name: idx_offline_uss_createdon; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_offline_uss_createdon ON public.offline_user_session USING btree (created_on);


--
-- Name: idx_protocol_mapper_client; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_protocol_mapper_client ON public.protocol_mapper USING btree (client_id);


--
-- Name: idx_realm_attr_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_realm_attr_realm ON public.realm_attribute USING btree (realm_id);


--
-- Name: idx_realm_clscope; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_realm_clscope ON public.client_scope USING btree (realm_id);


--
-- Name: idx_realm_def_grp_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_realm_def_grp_realm ON public.realm_default_groups USING btree (realm_id);


--
-- Name: idx_realm_def_roles_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_realm_def_roles_realm ON public.realm_default_roles USING btree (realm_id);


--
-- Name: idx_realm_evt_list_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_realm_evt_list_realm ON public.realm_events_listeners USING btree (realm_id);


--
-- Name: idx_realm_evt_types_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_realm_evt_types_realm ON public.realm_enabled_event_types USING btree (realm_id);


--
-- Name: idx_realm_master_adm_cli; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_realm_master_adm_cli ON public.realm USING btree (master_admin_client);


--
-- Name: idx_realm_supp_local_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_realm_supp_local_realm ON public.realm_supported_locales USING btree (realm_id);


--
-- Name: idx_redir_uri_client; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_redir_uri_client ON public.redirect_uris USING btree (client_id);


--
-- Name: idx_req_act_prov_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_req_act_prov_realm ON public.required_action_provider USING btree (realm_id);


--
-- Name: idx_res_policy_policy; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_res_policy_policy ON public.resource_policy USING btree (policy_id);


--
-- Name: idx_res_scope_scope; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_res_scope_scope ON public.resource_scope USING btree (scope_id);


--
-- Name: idx_res_serv_pol_res_serv; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_res_serv_pol_res_serv ON public.resource_server_policy USING btree (resource_server_id);


--
-- Name: idx_res_srv_res_res_srv; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_res_srv_res_res_srv ON public.resource_server_resource USING btree (resource_server_id);


--
-- Name: idx_res_srv_scope_res_srv; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_res_srv_scope_res_srv ON public.resource_server_scope USING btree (resource_server_id);


--
-- Name: idx_role_attribute; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_role_attribute ON public.role_attribute USING btree (role_id);


--
-- Name: idx_role_clscope; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_role_clscope ON public.client_scope_role_mapping USING btree (role_id);


--
-- Name: idx_scope_mapping_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_scope_mapping_role ON public.scope_mapping USING btree (role_id);


--
-- Name: idx_scope_policy_policy; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_scope_policy_policy ON public.scope_policy USING btree (policy_id);


--
-- Name: idx_update_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_update_time ON public.migration_model USING btree (update_time);


--
-- Name: idx_us_sess_id_on_cl_sess; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_us_sess_id_on_cl_sess ON public.offline_client_session USING btree (user_session_id);


--
-- Name: idx_usconsent_clscope; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_usconsent_clscope ON public.user_consent_client_scope USING btree (user_consent_id);


--
-- Name: idx_user_attribute; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_attribute ON public.user_attribute USING btree (user_id);


--
-- Name: idx_user_consent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_consent ON public.user_consent USING btree (user_id);


--
-- Name: idx_user_credential; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_credential ON public.credential USING btree (user_id);


--
-- Name: idx_user_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_email ON public.user_entity USING btree (email);


--
-- Name: idx_user_group_mapping; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_group_mapping ON public.user_group_membership USING btree (user_id);


--
-- Name: idx_user_reqactions; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_reqactions ON public.user_required_action USING btree (user_id);


--
-- Name: idx_user_role_mapping; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_role_mapping ON public.user_role_mapping USING btree (user_id);


--
-- Name: idx_usr_fed_map_fed_prv; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_usr_fed_map_fed_prv ON public.user_federation_mapper USING btree (federation_provider_id);


--
-- Name: idx_usr_fed_map_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_usr_fed_map_realm ON public.user_federation_mapper USING btree (realm_id);


--
-- Name: idx_usr_fed_prv_realm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_usr_fed_prv_realm ON public.user_federation_provider USING btree (realm_id);


--
-- Name: idx_web_orig_client; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_web_orig_client ON public.web_origins USING btree (client_id);


--
-- Name: client_session_auth_status auth_status_constraint; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_session_auth_status
    ADD CONSTRAINT auth_status_constraint FOREIGN KEY (client_session) REFERENCES public.client_session(id);


--
-- Name: identity_provider fk2b4ebc52ae5c3b34; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.identity_provider
    ADD CONSTRAINT fk2b4ebc52ae5c3b34 FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: client_attributes fk3c47c64beacca966; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_attributes
    ADD CONSTRAINT fk3c47c64beacca966 FOREIGN KEY (client_id) REFERENCES public.client(id);


--
-- Name: federated_identity fk404288b92ef007a6; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.federated_identity
    ADD CONSTRAINT fk404288b92ef007a6 FOREIGN KEY (user_id) REFERENCES public.user_entity(id);


--
-- Name: client_node_registrations fk4129723ba992f594; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_node_registrations
    ADD CONSTRAINT fk4129723ba992f594 FOREIGN KEY (client_id) REFERENCES public.client(id);


--
-- Name: client_session_note fk5edfb00ff51c2736; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_session_note
    ADD CONSTRAINT fk5edfb00ff51c2736 FOREIGN KEY (client_session) REFERENCES public.client_session(id);


--
-- Name: user_session_note fk5edfb00ff51d3472; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_session_note
    ADD CONSTRAINT fk5edfb00ff51d3472 FOREIGN KEY (user_session) REFERENCES public.user_session(id);


--
-- Name: client_session_role fk_11b7sgqw18i532811v7o2dv76; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_session_role
    ADD CONSTRAINT fk_11b7sgqw18i532811v7o2dv76 FOREIGN KEY (client_session) REFERENCES public.client_session(id);


--
-- Name: redirect_uris fk_1burs8pb4ouj97h5wuppahv9f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.redirect_uris
    ADD CONSTRAINT fk_1burs8pb4ouj97h5wuppahv9f FOREIGN KEY (client_id) REFERENCES public.client(id);


--
-- Name: user_federation_provider fk_1fj32f6ptolw2qy60cd8n01e8; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_federation_provider
    ADD CONSTRAINT fk_1fj32f6ptolw2qy60cd8n01e8 FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: client_session_prot_mapper fk_33a8sgqw18i532811v7o2dk89; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_session_prot_mapper
    ADD CONSTRAINT fk_33a8sgqw18i532811v7o2dk89 FOREIGN KEY (client_session) REFERENCES public.client_session(id);


--
-- Name: realm_required_credential fk_5hg65lybevavkqfki3kponh9v; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_required_credential
    ADD CONSTRAINT fk_5hg65lybevavkqfki3kponh9v FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: resource_attribute fk_5hrm2vlf9ql5fu022kqepovbr; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_attribute
    ADD CONSTRAINT fk_5hrm2vlf9ql5fu022kqepovbr FOREIGN KEY (resource_id) REFERENCES public.resource_server_resource(id);


--
-- Name: user_attribute fk_5hrm2vlf9ql5fu043kqepovbr; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_attribute
    ADD CONSTRAINT fk_5hrm2vlf9ql5fu043kqepovbr FOREIGN KEY (user_id) REFERENCES public.user_entity(id);


--
-- Name: user_required_action fk_6qj3w1jw9cvafhe19bwsiuvmd; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_required_action
    ADD CONSTRAINT fk_6qj3w1jw9cvafhe19bwsiuvmd FOREIGN KEY (user_id) REFERENCES public.user_entity(id);


--
-- Name: keycloak_role fk_6vyqfe4cn4wlq8r6kt5vdsj5c; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.keycloak_role
    ADD CONSTRAINT fk_6vyqfe4cn4wlq8r6kt5vdsj5c FOREIGN KEY (realm) REFERENCES public.realm(id);


--
-- Name: realm_smtp_config fk_70ej8xdxgxd0b9hh6180irr0o; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_smtp_config
    ADD CONSTRAINT fk_70ej8xdxgxd0b9hh6180irr0o FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: client_default_roles fk_8aelwnibji49avxsrtuf6xjow; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_default_roles
    ADD CONSTRAINT fk_8aelwnibji49avxsrtuf6xjow FOREIGN KEY (role_id) REFERENCES public.keycloak_role(id);


--
-- Name: realm_attribute fk_8shxd6l3e9atqukacxgpffptw; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_attribute
    ADD CONSTRAINT fk_8shxd6l3e9atqukacxgpffptw FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: composite_role fk_a63wvekftu8jo1pnj81e7mce2; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.composite_role
    ADD CONSTRAINT fk_a63wvekftu8jo1pnj81e7mce2 FOREIGN KEY (composite) REFERENCES public.keycloak_role(id);


--
-- Name: authentication_execution fk_auth_exec_flow; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.authentication_execution
    ADD CONSTRAINT fk_auth_exec_flow FOREIGN KEY (flow_id) REFERENCES public.authentication_flow(id);


--
-- Name: authentication_execution fk_auth_exec_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.authentication_execution
    ADD CONSTRAINT fk_auth_exec_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: authentication_flow fk_auth_flow_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.authentication_flow
    ADD CONSTRAINT fk_auth_flow_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: authenticator_config fk_auth_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.authenticator_config
    ADD CONSTRAINT fk_auth_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: client_session fk_b4ao2vcvat6ukau74wbwtfqo1; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_session
    ADD CONSTRAINT fk_b4ao2vcvat6ukau74wbwtfqo1 FOREIGN KEY (session_id) REFERENCES public.user_session(id);


--
-- Name: user_role_mapping fk_c4fqv34p1mbylloxang7b1q3l; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_role_mapping
    ADD CONSTRAINT fk_c4fqv34p1mbylloxang7b1q3l FOREIGN KEY (user_id) REFERENCES public.user_entity(id);


--
-- Name: client_scope_client fk_c_cli_scope_client; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_scope_client
    ADD CONSTRAINT fk_c_cli_scope_client FOREIGN KEY (client_id) REFERENCES public.client(id);


--
-- Name: client_scope_client fk_c_cli_scope_scope; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_scope_client
    ADD CONSTRAINT fk_c_cli_scope_scope FOREIGN KEY (scope_id) REFERENCES public.client_scope(id);


--
-- Name: client_scope_attributes fk_cl_scope_attr_scope; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_scope_attributes
    ADD CONSTRAINT fk_cl_scope_attr_scope FOREIGN KEY (scope_id) REFERENCES public.client_scope(id);


--
-- Name: client_scope_role_mapping fk_cl_scope_rm_role; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_scope_role_mapping
    ADD CONSTRAINT fk_cl_scope_rm_role FOREIGN KEY (role_id) REFERENCES public.keycloak_role(id);


--
-- Name: client_scope_role_mapping fk_cl_scope_rm_scope; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_scope_role_mapping
    ADD CONSTRAINT fk_cl_scope_rm_scope FOREIGN KEY (scope_id) REFERENCES public.client_scope(id);


--
-- Name: client_user_session_note fk_cl_usr_ses_note; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_user_session_note
    ADD CONSTRAINT fk_cl_usr_ses_note FOREIGN KEY (client_session) REFERENCES public.client_session(id);


--
-- Name: protocol_mapper fk_cli_scope_mapper; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.protocol_mapper
    ADD CONSTRAINT fk_cli_scope_mapper FOREIGN KEY (client_scope_id) REFERENCES public.client_scope(id);


--
-- Name: client_initial_access fk_client_init_acc_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_initial_access
    ADD CONSTRAINT fk_client_init_acc_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: component_config fk_component_config; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.component_config
    ADD CONSTRAINT fk_component_config FOREIGN KEY (component_id) REFERENCES public.component(id);


--
-- Name: component fk_component_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.component
    ADD CONSTRAINT fk_component_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: realm_default_groups fk_def_groups_group; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_default_groups
    ADD CONSTRAINT fk_def_groups_group FOREIGN KEY (group_id) REFERENCES public.keycloak_group(id);


--
-- Name: realm_default_groups fk_def_groups_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_default_groups
    ADD CONSTRAINT fk_def_groups_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: realm_default_roles fk_evudb1ppw84oxfax2drs03icc; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_default_roles
    ADD CONSTRAINT fk_evudb1ppw84oxfax2drs03icc FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: user_federation_mapper_config fk_fedmapper_cfg; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_federation_mapper_config
    ADD CONSTRAINT fk_fedmapper_cfg FOREIGN KEY (user_federation_mapper_id) REFERENCES public.user_federation_mapper(id);


--
-- Name: user_federation_mapper fk_fedmapperpm_fedprv; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_federation_mapper
    ADD CONSTRAINT fk_fedmapperpm_fedprv FOREIGN KEY (federation_provider_id) REFERENCES public.user_federation_provider(id);


--
-- Name: user_federation_mapper fk_fedmapperpm_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_federation_mapper
    ADD CONSTRAINT fk_fedmapperpm_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: associated_policy fk_frsr5s213xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.associated_policy
    ADD CONSTRAINT fk_frsr5s213xcx4wnkog82ssrfy FOREIGN KEY (associated_policy_id) REFERENCES public.resource_server_policy(id);


--
-- Name: scope_policy fk_frsrasp13xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scope_policy
    ADD CONSTRAINT fk_frsrasp13xcx4wnkog82ssrfy FOREIGN KEY (policy_id) REFERENCES public.resource_server_policy(id);


--
-- Name: resource_server_perm_ticket fk_frsrho213xcx4wnkog82sspmt; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_perm_ticket
    ADD CONSTRAINT fk_frsrho213xcx4wnkog82sspmt FOREIGN KEY (resource_server_id) REFERENCES public.resource_server(id);


--
-- Name: resource_server_resource fk_frsrho213xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_resource
    ADD CONSTRAINT fk_frsrho213xcx4wnkog82ssrfy FOREIGN KEY (resource_server_id) REFERENCES public.resource_server(id);


--
-- Name: resource_server_perm_ticket fk_frsrho213xcx4wnkog83sspmt; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_perm_ticket
    ADD CONSTRAINT fk_frsrho213xcx4wnkog83sspmt FOREIGN KEY (resource_id) REFERENCES public.resource_server_resource(id);


--
-- Name: resource_server_perm_ticket fk_frsrho213xcx4wnkog84sspmt; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_perm_ticket
    ADD CONSTRAINT fk_frsrho213xcx4wnkog84sspmt FOREIGN KEY (scope_id) REFERENCES public.resource_server_scope(id);


--
-- Name: associated_policy fk_frsrpas14xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.associated_policy
    ADD CONSTRAINT fk_frsrpas14xcx4wnkog82ssrfy FOREIGN KEY (policy_id) REFERENCES public.resource_server_policy(id);


--
-- Name: scope_policy fk_frsrpass3xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scope_policy
    ADD CONSTRAINT fk_frsrpass3xcx4wnkog82ssrfy FOREIGN KEY (scope_id) REFERENCES public.resource_server_scope(id);


--
-- Name: resource_server_perm_ticket fk_frsrpo2128cx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_perm_ticket
    ADD CONSTRAINT fk_frsrpo2128cx4wnkog82ssrfy FOREIGN KEY (policy_id) REFERENCES public.resource_server_policy(id);


--
-- Name: resource_server_policy fk_frsrpo213xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_policy
    ADD CONSTRAINT fk_frsrpo213xcx4wnkog82ssrfy FOREIGN KEY (resource_server_id) REFERENCES public.resource_server(id);


--
-- Name: resource_scope fk_frsrpos13xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_scope
    ADD CONSTRAINT fk_frsrpos13xcx4wnkog82ssrfy FOREIGN KEY (resource_id) REFERENCES public.resource_server_resource(id);


--
-- Name: resource_policy fk_frsrpos53xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_policy
    ADD CONSTRAINT fk_frsrpos53xcx4wnkog82ssrfy FOREIGN KEY (resource_id) REFERENCES public.resource_server_resource(id);


--
-- Name: resource_policy fk_frsrpp213xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_policy
    ADD CONSTRAINT fk_frsrpp213xcx4wnkog82ssrfy FOREIGN KEY (policy_id) REFERENCES public.resource_server_policy(id);


--
-- Name: resource_scope fk_frsrps213xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_scope
    ADD CONSTRAINT fk_frsrps213xcx4wnkog82ssrfy FOREIGN KEY (scope_id) REFERENCES public.resource_server_scope(id);


--
-- Name: resource_server_scope fk_frsrso213xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_server_scope
    ADD CONSTRAINT fk_frsrso213xcx4wnkog82ssrfy FOREIGN KEY (resource_server_id) REFERENCES public.resource_server(id);


--
-- Name: composite_role fk_gr7thllb9lu8q4vqa4524jjy8; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.composite_role
    ADD CONSTRAINT fk_gr7thllb9lu8q4vqa4524jjy8 FOREIGN KEY (child_role) REFERENCES public.keycloak_role(id);


--
-- Name: user_consent_client_scope fk_grntcsnt_clsc_usc; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_consent_client_scope
    ADD CONSTRAINT fk_grntcsnt_clsc_usc FOREIGN KEY (user_consent_id) REFERENCES public.user_consent(id);


--
-- Name: user_consent fk_grntcsnt_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_consent
    ADD CONSTRAINT fk_grntcsnt_user FOREIGN KEY (user_id) REFERENCES public.user_entity(id);


--
-- Name: group_attribute fk_group_attribute_group; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_attribute
    ADD CONSTRAINT fk_group_attribute_group FOREIGN KEY (group_id) REFERENCES public.keycloak_group(id);


--
-- Name: keycloak_group fk_group_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.keycloak_group
    ADD CONSTRAINT fk_group_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: group_role_mapping fk_group_role_group; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_role_mapping
    ADD CONSTRAINT fk_group_role_group FOREIGN KEY (group_id) REFERENCES public.keycloak_group(id);


--
-- Name: group_role_mapping fk_group_role_role; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_role_mapping
    ADD CONSTRAINT fk_group_role_role FOREIGN KEY (role_id) REFERENCES public.keycloak_role(id);


--
-- Name: realm_default_roles fk_h4wpd7w4hsoolni3h0sw7btje; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_default_roles
    ADD CONSTRAINT fk_h4wpd7w4hsoolni3h0sw7btje FOREIGN KEY (role_id) REFERENCES public.keycloak_role(id);


--
-- Name: realm_enabled_event_types fk_h846o4h0w8epx5nwedrf5y69j; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_enabled_event_types
    ADD CONSTRAINT fk_h846o4h0w8epx5nwedrf5y69j FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: realm_events_listeners fk_h846o4h0w8epx5nxev9f5y69j; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_events_listeners
    ADD CONSTRAINT fk_h846o4h0w8epx5nxev9f5y69j FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: identity_provider_mapper fk_idpm_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.identity_provider_mapper
    ADD CONSTRAINT fk_idpm_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: idp_mapper_config fk_idpmconfig; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.idp_mapper_config
    ADD CONSTRAINT fk_idpmconfig FOREIGN KEY (idp_mapper_id) REFERENCES public.identity_provider_mapper(id);


--
-- Name: keycloak_role fk_kjho5le2c0ral09fl8cm9wfw9; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.keycloak_role
    ADD CONSTRAINT fk_kjho5le2c0ral09fl8cm9wfw9 FOREIGN KEY (client) REFERENCES public.client(id);


--
-- Name: web_origins fk_lojpho213xcx4wnkog82ssrfy; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.web_origins
    ADD CONSTRAINT fk_lojpho213xcx4wnkog82ssrfy FOREIGN KEY (client_id) REFERENCES public.client(id);


--
-- Name: client_default_roles fk_nuilts7klwqw2h8m2b5joytky; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_default_roles
    ADD CONSTRAINT fk_nuilts7klwqw2h8m2b5joytky FOREIGN KEY (client_id) REFERENCES public.client(id);


--
-- Name: scope_mapping fk_ouse064plmlr732lxjcn1q5f1; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scope_mapping
    ADD CONSTRAINT fk_ouse064plmlr732lxjcn1q5f1 FOREIGN KEY (client_id) REFERENCES public.client(id);


--
-- Name: scope_mapping fk_p3rh9grku11kqfrs4fltt7rnq; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scope_mapping
    ADD CONSTRAINT fk_p3rh9grku11kqfrs4fltt7rnq FOREIGN KEY (role_id) REFERENCES public.keycloak_role(id);


--
-- Name: client fk_p56ctinxxb9gsk57fo49f9tac; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client
    ADD CONSTRAINT fk_p56ctinxxb9gsk57fo49f9tac FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: protocol_mapper fk_pcm_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.protocol_mapper
    ADD CONSTRAINT fk_pcm_realm FOREIGN KEY (client_id) REFERENCES public.client(id);


--
-- Name: credential fk_pfyr0glasqyl0dei3kl69r6v0; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.credential
    ADD CONSTRAINT fk_pfyr0glasqyl0dei3kl69r6v0 FOREIGN KEY (user_id) REFERENCES public.user_entity(id);


--
-- Name: protocol_mapper_config fk_pmconfig; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.protocol_mapper_config
    ADD CONSTRAINT fk_pmconfig FOREIGN KEY (protocol_mapper_id) REFERENCES public.protocol_mapper(id);


--
-- Name: default_client_scope fk_r_def_cli_scope_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.default_client_scope
    ADD CONSTRAINT fk_r_def_cli_scope_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: default_client_scope fk_r_def_cli_scope_scope; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.default_client_scope
    ADD CONSTRAINT fk_r_def_cli_scope_scope FOREIGN KEY (scope_id) REFERENCES public.client_scope(id);


--
-- Name: client_scope fk_realm_cli_scope; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_scope
    ADD CONSTRAINT fk_realm_cli_scope FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: required_action_provider fk_req_act_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.required_action_provider
    ADD CONSTRAINT fk_req_act_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: resource_uris fk_resource_server_uris; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resource_uris
    ADD CONSTRAINT fk_resource_server_uris FOREIGN KEY (resource_id) REFERENCES public.resource_server_resource(id);


--
-- Name: role_attribute fk_role_attribute_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_attribute
    ADD CONSTRAINT fk_role_attribute_id FOREIGN KEY (role_id) REFERENCES public.keycloak_role(id);


--
-- Name: realm_supported_locales fk_supported_locales_realm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm_supported_locales
    ADD CONSTRAINT fk_supported_locales_realm FOREIGN KEY (realm_id) REFERENCES public.realm(id);


--
-- Name: user_federation_config fk_t13hpu1j94r2ebpekr39x5eu5; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_federation_config
    ADD CONSTRAINT fk_t13hpu1j94r2ebpekr39x5eu5 FOREIGN KEY (user_federation_provider_id) REFERENCES public.user_federation_provider(id);


--
-- Name: realm fk_traf444kk6qrkms7n56aiwq5y; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.realm
    ADD CONSTRAINT fk_traf444kk6qrkms7n56aiwq5y FOREIGN KEY (master_admin_client) REFERENCES public.client(id);


--
-- Name: user_group_membership fk_user_group_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_group_membership
    ADD CONSTRAINT fk_user_group_user FOREIGN KEY (user_id) REFERENCES public.user_entity(id);


--
-- Name: policy_config fkdc34197cf864c4e43; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.policy_config
    ADD CONSTRAINT fkdc34197cf864c4e43 FOREIGN KEY (policy_id) REFERENCES public.resource_server_policy(id);


--
-- Name: identity_provider_config fkdc4897cf864c4e43; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.identity_provider_config
    ADD CONSTRAINT fkdc4897cf864c4e43 FOREIGN KEY (identity_provider_id) REFERENCES public.identity_provider(internal_id);


--
-- PostgreSQL database dump complete
--
