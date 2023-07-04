<#import "template.ftl" as layout>
<@layout.registrationLayout; section>
    <#if section = "header">
        ${msg("registerTitle")}
    <#elseif section = "form">
        <form id="kc-register-form" action="${url.registrationAction}" method="post">
            <div class="rf-input-group">

                <label for="firstName" class="rf-label">${msg("firstName")}</label>
                <input type="text" id="firstName" class="rf-input" name="firstName"
                       value="${(register.formData.firstName!'')}"
                       aria-invalid="<#if messagesPerField.existsError('firstName')>true</#if>"
                />

                <#if messagesPerField.existsError('firstName')>
                    <span id="input-error-firstname" class="${properties.kcInputErrorMessageClass!}" aria-live="polite">
                        ${kcSanitize(messagesPerField.get('firstName'))?no_esc}
                    </span>
                </#if>

            </div>

            <div class="rf-input-group">

                <label for="lastName" class="rf-label">${msg("lastName")}</label>
                <input type="text" id="lastName" class="rf-input" name="lastName"
                       value="${(register.formData.lastName!'')}"
                       aria-invalid="<#if messagesPerField.existsError('lastName')>true</#if>"
                />

                <#if messagesPerField.existsError('lastName')>
                    <span id="input-error-lastname" class="${properties.kcInputErrorMessageClass!}" aria-live="polite">
                        ${kcSanitize(messagesPerField.get('lastName'))?no_esc}
                    </span>
                </#if>

            </div>

            <div class="rf-input-group">

                <label for="email" class="rf-label">${msg("email")}</label>
                <input type="text" id="email" class="rf-input" name="email"
                       value="${(register.formData.email!'')}" autocomplete="email"
                       aria-invalid="<#if messagesPerField.existsError('email')>true</#if>"
                />

                <#if messagesPerField.existsError('email')>
                    <span id="input-error-email" class="${properties.kcInputErrorMessageClass!}" aria-live="polite">
                        ${kcSanitize(messagesPerField.get('email'))?no_esc}
                    </span>
                </#if>

            </div>

            <#if !realm.registrationEmailAsUsername>
                <div class="rf-input-group">

                    <label for="username" class="rf-label">${msg("username")}</label>
                    <input type="text" id="username" class="rf-input" name="username"
                           value="${(register.formData.username!'')}" autocomplete="username"
                           aria-invalid="<#if messagesPerField.existsError('username')>true</#if>"
                    />

                    <#if messagesPerField.existsError('username')>
                        <span id="input-error-username" class="${properties.kcInputErrorMessageClass!}" aria-live="polite">
                            ${kcSanitize(messagesPerField.get('username'))?no_esc}
                        </span>
                    </#if>

                </div>
            </#if>

            <#if passwordRequired??>
                <div class="rf-input-group">

                        <label for="password" class="rf-label">${msg("password")}</label>
                        <input type="password" id="password" class="rf-input" name="password"
                               autocomplete="new-password"
                               aria-invalid="<#if messagesPerField.existsError('password','password-confirm')>true</#if>"
                        />

                        <#if messagesPerField.existsError('password')>
                            <span id="input-error-password" class="${properties.kcInputErrorMessageClass!}" aria-live="polite">
                                ${kcSanitize(messagesPerField.get('password'))?no_esc}
                            </span>
                        </#if>
                </div>

                <div class="rf-input-group">

                        <label for="password-confirm" class="rf-label">${msg("passwordConfirm")}</label>
                        <input type="password" id="password-confirm" class="rf-input"
                               name="password-confirm"
                               aria-invalid="<#if messagesPerField.existsError('password-confirm')>true</#if>"
                        />

                        <#if messagesPerField.existsError('password-confirm')>
                            <span id="input-error-password-confirm" class="${properties.kcInputErrorMessageClass!}" aria-live="polite">
                                ${kcSanitize(messagesPerField.get('password-confirm'))?no_esc}
                            </span>
                        </#if>

                </div>
            </#if>

            <#if recaptchaRequired??>
                <div class="g-recaptcha" data-size="compact" data-sitekey="${recaptchaSiteKey}"></div>
            </#if>

            <div class="rf-input-group">

                <div id="kc-form-options" class="${properties.kcFormOptionsClass!}">
                    <div class="${properties.kcFormOptionsWrapperClass!}">
                        <span><a href="${url.loginUrl}">${kcSanitize(msg("backToLogin"))?no_esc}</a></span>
                    </div>
                </div>
                <div id="kc-form-buttons" class="${properties.kcFormButtonsClass!}">
                    <input class="rf-btn rf-btn--primary" type="submit" value="${msg("doRegister")}"/>
                </div>

            </div>
        </form>
    </#if>

</@layout.registrationLayout>
