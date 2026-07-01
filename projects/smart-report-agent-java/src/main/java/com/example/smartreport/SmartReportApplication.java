package com.example.smartreport;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
// 扫描 @ConfigurationProperties，等价于 Python 版 Settings.xxx = ... 的集中配置
@ConfigurationPropertiesScan
public class SmartReportApplication {

    public static void main(String[] args) {
        SpringApplication.run(SmartReportApplication.class, args);
    }
}
