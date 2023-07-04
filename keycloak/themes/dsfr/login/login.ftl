<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=social.displayInfo displayWide=(realm.password && social.providers??); section>
    <#if section = "header">
        ${msg("doLogIn")}
    <#elseif section = "form">
        <div id="kc-login" class="rf-grid-row rf-grid-row--gutters">
      <div id="kc-form-wrapper" class="rf-col">
      <#if realm.password && social.providers??>
          <div id="kc-social-providers"  class="rf-col">
              <ul class="rf-tag-list">
                  <#list social.providers as p>
                      <li class="zocial-item zocial-item-${p.alias}" >
                          <a href="${p.loginUrl}" id="zocial-${p.alias}" class="rf-tag ${p.providerId}">
                              <span class="AgentConnectName">${p.displayName}</span>
                          </a>
                          <#if p.alias?? && p.alias == "agentconnect">
                              <span class="AgentConnectLink"><a href="https://agentconnect.gouv.fr/">Qu'est-ce qu'AgentConnect ?</a></span>
						  <#else>
                          </#if>
                      </li>
                  </#list>
              </ul>
          </div>
      </#if>
        <#if realm.password>
          <form id="kc-form-login" onsubmit="login.disabled = true; return true;" action="${url.loginAction}" method="post">
              <div class="rf-mb-3w rf-input-group">
                  <label for="username" class="rf-label"><#if !realm.loginWithEmailAllowed>${msg("username")}<#elseif !realm.registrationEmailAsUsername>${msg("usernameOrEmail")}<#else>${msg("email")}</#if></label>

                  <#if usernameEditDisabled??>
                      <input id="username" class="rf-input" name="username" value="${(login.username!'')}" type="text" disabled />
                  <#else>
                      <input id="username" class="rf-input" name="username" value="${(login.username!'')}"  type="text" autofocus autocomplete="off" />
                  </#if>
              </div>

              <div class="rf-mb-3w rf-input-group">
                  <label for="password" class="rf-label">${msg("password")}</label>
                  <input id="password" class="rf-input" name="password" type="password" autocomplete="off" />
              </div>

              <div>
                  <div id="kc-form-options">
                      <#if realm.rememberMe && !usernameEditDisabled??>
                          <div class="checkbox">
                              <label>
                                  <#if login.rememberMe??>
                                      <input id="rememberMe" name="rememberMe" type="checkbox" checked> ${msg("rememberMe")}
                                  <#else>
                                      <input id="rememberMe" name="rememberMe" type="checkbox"> ${msg("rememberMe")}
                                  </#if>
                              </label>
                          </div>
                      </#if>
                      </div>
                      <div class="${properties.kcFormOptionsWrapperClass!}">
                          <#if realm.resetPasswordAllowed>
                              <span><a href="${url.loginResetCredentialsUrl}">${msg("doForgotPassword")}</a></span>
                          </#if>
                      </div>

                </div>

                <div id="kc-form-buttons" class="rf-input-group">
                    <input type="hidden" id="id-hidden-input" name="credentialId" <#if auth.selectedCredential?has_content>value="${auth.selectedCredential}"</#if>/>
                    <button class="rf-btn rf-btn--primary" name="login" id="kc-login" type="submit">${msg("doLogIn")}</button>
                </div>
          </form>
        </#if>
      </div>
      </div>
    <#elseif section = "info" >
        <#if realm.password && realm.registrationAllowed && !registrationDisabled??>
            <div id="kc-registration">
                <span>${msg("noAccount")} <a tabindex="6" class="rf-link" href="${url.registrationUrl}">${msg("doRegister")}</a></span>
            </div>
        </#if>
    </#if>

</@layout.registrationLayout>
