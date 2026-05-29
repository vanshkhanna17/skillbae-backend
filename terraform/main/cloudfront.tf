resource "aws_cloudfront_distribution" "api_cdn" {
  enabled = true
  origin {
    domain_name = "${aws_instance.app_server.public_ip}.nip.io"
    origin_id   = "origin-instance-${module.label.namespace}-${module.label.environment}-${module.label.name}"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "origin-instance-${module.label.namespace}-${module.label.environment}-${module.label.name}"
    forwarded_values {
      query_string = true # forward query params to FastAPI
      headers = ["Authorization", "Content-Type", "Origin",
      "Accept", "X-Requested-With"] # forward auth headers
      cookies {
        forward = "all" # forward HttpOnly cookies
      }
    }
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0 # no caching — this is an API
    max_ttl                = 0
  }
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Environment = module.label.environment
    Name        = "${module.label.namespace}-${module.label.environment}-${module.label.name}-cdn"
  }
}
