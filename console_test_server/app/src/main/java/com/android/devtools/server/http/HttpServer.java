/*
 * Copyright (c) 2016 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.android.devtools.server.http;

import org.mortbay.jetty.Server;
import org.mortbay.jetty.handler.ContextHandler;
import org.mortbay.jetty.nio.SelectChannelConnector;
import org.mortbay.jetty.servlet.HashSessionManager;
import org.mortbay.jetty.servlet.ServletHandler;
import org.mortbay.jetty.servlet.SessionHandler;

import java.util.Map;

/**
 * <p>Http Server Implementation.</p> <p> It is the place to register servlet.</p>
 */
public class HttpServer {

  private static final String SERVER_CONTEXT_PATH = "/";
  private final int port;
  private final int acceptors;
  private final int maxIdleTime;
  private final int soLingerTime;
  private final Map<Class<?>, String> servletUrlPathMapping;
  private Server server;

  private HttpServer(final Server server, final int port, final int acceptors,
      final int maxIdleTime,
      final int soLingerTime, final Map<Class<?>, String> servletUrlPathMapping) {
    this.server = server;
    this.port = port;
    this.acceptors = acceptors;
    this.maxIdleTime = maxIdleTime;
    this.soLingerTime = soLingerTime;
    this.servletUrlPathMapping = servletUrlPathMapping;
  }

  public void start() throws Exception {
    configureServer();
    server.start();
    server.join();
  }

  private void configureServer() {
    ServletHandler servletHandler = setServletHandler();
    setSelectChannelConnector();
    SessionHandler sessionsHandler = setSessionHandler(servletHandler);
    setSessionHandler(sessionsHandler);
  }

  private void setSessionHandler(SessionHandler sessionsHandler) {
    ContextHandler contextHandler = new ContextHandler(SERVER_CONTEXT_PATH);
    contextHandler.setHandler(sessionsHandler);
    server.setHandler(contextHandler);
  }

  private SessionHandler setSessionHandler(ServletHandler servletHandler) {
    HashSessionManager manager = new HashSessionManager();
    SessionHandler sessionsHandler = new SessionHandler(manager);
    sessionsHandler.setHandler(servletHandler);
    return sessionsHandler;
  }

  private void setSelectChannelConnector() {
    SelectChannelConnector connector = new SelectChannelConnector();
    connector.setPort(port);
    connector.setAcceptors(acceptors);
    connector.setMaxIdleTime(maxIdleTime);
    connector.setSoLingerTime(soLingerTime);
    server.addConnector(connector);
  }

  private ServletHandler setServletHandler() {
    ServletHandler servletHandler = new ServletHandler();
    for (Class<?> servlet : servletUrlPathMapping.keySet()) {
      servletHandler.addServletWithMapping(servlet, servletUrlPathMapping.get(servlet));
    }
    return servletHandler;
  }

  public void stop() throws Exception {
    if (server != null) {
      server.stop();
      server = null;
    }
  }

  /**
   * A builder for creating HttpServer.
   */
  public static class HttpServerBuilder {

    private int port;
    private int acceptors;
    private int maxIdleTime;
    private int soLingerTime;
    private Map<Class<?>, String> servletUrlPathMapping;
    private Server server;

    public HttpServer build() {
      checkServletMappingNullOrEmpty(servletUrlPathMapping);
      return new HttpServer(server, port, acceptors, maxIdleTime, soLingerTime,
          servletUrlPathMapping);
    }

    public HttpServerBuilder withServer(final Server server) {
      this.server = server;
      return this;
    }

    public HttpServerBuilder withPort(final int port) {
      this.port = port;
      return this;
    }

    public HttpServerBuilder withAcceptors(final int acceptors) {
      this.acceptors = acceptors;
      return this;
    }

    public HttpServerBuilder withMaxIdleTime(final int maxIdleTime) {
      this.maxIdleTime = maxIdleTime;
      return this;
    }

    public HttpServerBuilder withSoLingerTime(final int soLingerTime) {
      this.soLingerTime = soLingerTime;
      return this;
    }

    public HttpServerBuilder withServletUrlPathMapping(
        final Map<Class<?>, String> servletUrlPathMapping) {
      checkServletMappingNullOrEmpty(servletUrlPathMapping);
      this.servletUrlPathMapping = servletUrlPathMapping;
      return this;
    }

    private void checkServletMappingNullOrEmpty(Map<Class<?>, String> servletUrlPathMapping) {
      if (null == servletUrlPathMapping) {
        throw new RuntimeException("servletUrlPathMapping should not be null");
      }
    }
  }
}
